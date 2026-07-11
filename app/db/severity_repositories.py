from app.db.severity_models import CaseSeverity

def save_case_severity(db, case_id: int, severity_label: str, confidence: float, source: str):
    new_severity = CaseSeverity(
        report_case_id=case_id,
        severity_label=severity_label,
        confidence=confidence,
        source=source
    )
    db.add(new_severity)
    db.commit()
    db.refresh(new_severity)
    return new_severity