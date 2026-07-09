from typing import Any

from sqlalchemy.orm import Session

from app.db.models import (
    ClinicalPatternResult,
    EvaluationCase,
    EvaluationResult,
    GeneratedReport,
    KnowledgeDocMetadata,
    LabResult,
    ReportCase,
    RetrievedSource,
)


def _save(db: Session, obj: Any):
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_report_case(db: Session, data: dict) -> ReportCase:
    case = ReportCase(
        age=data["age"],
        sex=data["sex"],
        selected_panel=data["selected_panel"],
        symptoms=data.get("symptoms", []),
        clinical_notes=data.get("clinical_notes"),
    )
    return _save(db, case)


def get_report_case_by_id(db: Session, case_id: int) -> ReportCase | None:
    return db.query(ReportCase).filter(ReportCase.id == case_id).first()


def add_lab_results(db: Session, case_id: int, results_list: list[dict]) -> list[LabResult]:
    saved_results = []
    for item in results_list:
        result = LabResult(
            report_case_id=case_id,
            panel=item.get("panel", ""),
            test_name=item["test_name"],
            value=item["value"],
            unit=item.get("unit"),
            status=item.get("status"),
            reference_low=item.get("reference_low"),
            reference_high=item.get("reference_high"),
            critical_low=item.get("critical_low"),
            critical_high=item.get("critical_high"),
            evidence=item.get("evidence"),
        )
        db.add(result)
        saved_results.append(result)

    db.commit()

    for result in saved_results:
        db.refresh(result)

    return saved_results


def add_pattern_results(db: Session, case_id: int, patterns: list[dict]) -> list[ClinicalPatternResult]:
    saved_patterns = []
    for item in patterns:
        pattern = ClinicalPatternResult(
            report_case_id=case_id,
            pattern_code=item["pattern_code"],
            pattern_name=item["pattern_name"],
            rank=item["rank"],
            score=item.get("score"),
            confidence_level=item.get("confidence_level"),
            evidence_for=item.get("evidence_for", []),
            missing_evidence=item.get("missing_evidence", []),
            warnings=item.get("warnings"),
        )
        db.add(pattern)
        saved_patterns.append(pattern)

    db.commit()

    for pattern in saved_patterns:
        db.refresh(pattern)

    return saved_patterns


def add_retrieved_sources(db: Session, case_id: int, sources: list[dict]) -> list[RetrievedSource]:
    saved_sources = []
    for item in sources:
        source = RetrievedSource(
            report_case_id=case_id,
            pattern_result_id=item.get("pattern_result_id"),
            source_id=item["source_id"],
            title=item["title"],
            snippet=item.get("snippet"),
            similarity_score=item.get("similarity_score"),
        )
        db.add(source)
        saved_sources.append(source)

    db.commit()

    for source in saved_sources:
        db.refresh(source)

    return saved_sources


def save_generated_report(db: Session, case_id: int, report_markdown: str, report_file_path: str | None = None) -> GeneratedReport:
    report = GeneratedReport(
        report_case_id=case_id,
        report_markdown=report_markdown,
        report_file_path=report_file_path,
    )
    return _save(db, report)


def get_generated_report_by_id(db: Session, report_id: int) -> GeneratedReport | None:
    return db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()


def save_knowledge_doc_metadata(db: Session, data: dict) -> KnowledgeDocMetadata:
    metadata = (
        db.query(KnowledgeDocMetadata)
        .filter(KnowledgeDocMetadata.source_id == data["source_id"])
        .first()
    )

    if metadata is None:
        metadata = KnowledgeDocMetadata(
            source_id=data["source_id"],
            title=data["title"],
            file_path=data["file_path"],
            panel=data.get("panel"),
            chunk_count=data.get("chunk_count"),
        )
    else:
        metadata.title = data["title"]
        metadata.file_path = data["file_path"]
        metadata.panel = data.get("panel")
        metadata.chunk_count = data.get("chunk_count")

    return _save(db, metadata)


def create_evaluation_case(db: Session, data: dict) -> EvaluationCase:
    eval_case = EvaluationCase(
        input_json=data["input_json"],
        expected_patterns=data["expected_patterns"],
        difficulty=data.get("difficulty"),
        panel=data.get("panel"),
        lab_count=data.get("lab_count"),
        symptom_count=data.get("symptom_count"),
    )
    return _save(db, eval_case)


def save_evaluation_result(db: Session, data: dict) -> EvaluationResult:
    result = EvaluationResult(
        eval_case_id=data["eval_case_id"],
        predicted_patterns=data.get("predicted_patterns", []),
        expected_patterns=data.get("expected_patterns", []),
        is_top3_correct=data.get("is_top3_correct", False),
        latency_ms=data.get("latency_ms"),
        run_id=data.get("run_id"),
    )
    return _save(db, result)
