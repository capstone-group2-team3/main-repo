from app.db.severity_models import CaseSeverity


def save_case_severity(db, case_id: int, severity_label: str, confidence: float, source: str):
    severity = (
        db.query(CaseSeverity)
        .filter(CaseSeverity.report_case_id == case_id)
        .first()
    )

    if severity is None:
        severity = CaseSeverity(report_case_id=case_id)
        db.add(severity)

    severity.severity_label = severity_label
    severity.confidence = confidence
    severity.source = source

    db.commit()
    db.refresh(severity)
    return severity


def get_case_severity_by_case_id(db, case_id: int):
    return (
        db.query(CaseSeverity)
        .filter(CaseSeverity.report_case_id == case_id)
        .first()
    )
