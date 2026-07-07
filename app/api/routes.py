from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import create_report_case, get_generated_report_by_id, get_report_case_by_id
from app.models.schemas import ReportRequest

router = APIRouter()

SAFETY_NOTICE = (
    "This tool supports clinician review only. It does not provide a final diagnosis, "
    "does not prescribe medication, and does not replace physician judgment."
)


def to_dict(payload: ReportRequest) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/reports/analyze")
def analyze_report(payload: ReportRequest, db: Session = Depends(get_db)):
    """
    Day 1 placeholder endpoint.

    Later tasks will replace this echo response with:
    lab analysis, clinical pattern scoring, RAG retrieval, safety checks, and report generation.
    """
    data = to_dict(payload)

    case = create_report_case(
        db,
        {
            "age": payload.age,
            "sex": payload.sex,
            "selected_panel": payload.selected_panel,
            "symptoms": payload.symptoms,
            "clinical_notes": payload.clinical_notes,
        },
    )

    return {
        "message": "Placeholder analysis endpoint is working. Full pipeline will be implemented in later tasks.",
        "report_case_id": case.id,
        "received": data,
        "safety_notice": SAFETY_NOTICE,
    }


@router.get("/templates")
def get_templates_placeholder():
    return {
        "message": "Panel templates will be implemented in Day 2.",
        "panels": [],
    }


@router.get("/reports/{report_id}")
def get_report_placeholder(report_id: int, db: Session = Depends(get_db)):
    report = get_generated_report_by_id(db, report_id)

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found. Report generation will be implemented later.")

    return {
        "id": report.id,
        "report_case_id": report.report_case_id,
        "report_markdown": report.report_markdown,
        "report_file_path": report.report_file_path,
        "created_at": report.created_at,
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
