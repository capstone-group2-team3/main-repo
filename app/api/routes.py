from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import (
    get_generated_report_by_id,
    get_latest_generated_report_by_case_id,
    get_report_case_by_id,
)
from app.models.schemas import ReportRequest
from app.services.agent_orchestrator import AgentOrchestrator, SAFETY_NOTICE
from app.services.knowledge_indexer import KnowledgeIndexer
from app.services.panel_template_service import PanelTemplateService
from app.services.report_generator_agent import REPORT_OUTPUT_DIR
router = APIRouter()

orchestrator = AgentOrchestrator()
panel_template_service = PanelTemplateService()
knowledge_indexer = KnowledgeIndexer()


def _isoformat_or_none(value):
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


def _safe_report_path(raw_path: str | None, suffix: str) -> Path | None:
    if not raw_path:
        return None

    project_root = Path(__file__).resolve().parents[2]
    report_dir = (project_root / REPORT_OUTPUT_DIR).resolve()
    candidate = Path(raw_path)

    if not candidate.is_absolute():
        candidate = project_root / candidate

    candidate = candidate.with_suffix(suffix).resolve()

    try:
        candidate.relative_to(report_dir)
    except ValueError:
        return None

    return candidate


def _download_generated_report(case_id: int, suffix: str, media_type: str, db: Session):
    report = get_latest_generated_report_by_case_id(db, case_id)

    if report is None:
        raise HTTPException(status_code=404, detail=f"No generated report found for case {case_id}.")

    path = _safe_report_path(report.report_file_path, suffix)

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Generated report file not found for case {case_id}.")

    return FileResponse(
        path=path,
        media_type=media_type,
        filename=path.name,
    )


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/templates")
def get_templates():
    return {
        "panels": panel_template_service.get_available_panels(),
        "templates": panel_template_service.get_all_templates(),
    }

@router.post("/index/medical-knowledge")
def index_medical_knowledge(db: Session = Depends(get_db)):
    try:
        return knowledge_indexer.index_medical_knowledge(db)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

@router.get("/templates/{panel_name:path}")
def get_template(panel_name: str):
    template = panel_template_service.get_template(panel_name)

    if template is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {panel_name}")

    return template


@router.post("/reports/analyze")
def analyze_report(payload: ReportRequest, db: Session = Depends(get_db)):
    try:
        return orchestrator.analyze_report(payload, db)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/reports/{case_id}/download/markdown")
def download_markdown_report(case_id: int, db: Session = Depends(get_db)):
    return _download_generated_report(case_id, ".md", "text/markdown", db)


@router.get("/reports/{case_id}/download/html")
def download_html_report(case_id: int, db: Session = Depends(get_db)):
    return _download_generated_report(case_id, ".html", "text/html", db)


@router.get("/reports/{report_id}")
def get_report_placeholder(report_id: int, db: Session = Depends(get_db)):
    report = get_generated_report_by_id(db, report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found. Report generation will be implemented later.",
        )

    return {
        "id": report.id,
        "report_case_id": report.report_case_id,
        "report_markdown": report.report_markdown,
        "report_file_path": report.report_file_path,
        "created_at": _isoformat_or_none(report.created_at),
        "safety_notice": SAFETY_NOTICE,
    }


@router.get("/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = get_report_case_by_id(db, case_id)

    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    return {
        "id": case.id,
        "age": case.age,
        "sex": case.sex,
        "selected_panel": case.selected_panel,
        "symptoms": case.symptoms,
        "clinical_notes": case.clinical_notes,
        "created_at": _isoformat_or_none(case.created_at),
    }
