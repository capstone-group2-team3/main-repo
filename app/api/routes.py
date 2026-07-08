from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import get_generated_report_by_id, get_report_case_by_id
from app.models.schemas import ReportRequest
from app.services.agent_orchestrator import AgentOrchestrator, SAFETY_NOTICE
from app.services.panel_template_service import PanelTemplateService

router = APIRouter()

orchestrator = AgentOrchestrator()
panel_template_service = PanelTemplateService()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/templates")
def get_templates():
    return {
        "panels": panel_template_service.get_available_panels(),
        "templates": panel_template_service.get_all_templates(),
    }


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
        "created_at": report.created_at,
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
        "created_at": case.created_at,
    }
