from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.database import Base


class ReportCase(Base):
    __tablename__ = "report_cases"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer, nullable=False)
    sex = Column(String(30), nullable=False)
    selected_panel = Column(String(120), nullable=False)
    symptoms = Column(JSON, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lab_results = relationship("LabResult", back_populates="report_case", cascade="all, delete-orphan")
    clinical_patterns = relationship("ClinicalPatternResult", back_populates="report_case", cascade="all, delete-orphan")
    retrieved_sources = relationship("RetrievedSource", back_populates="report_case", cascade="all, delete-orphan")
    generated_reports = relationship("GeneratedReport", back_populates="report_case", cascade="all, delete-orphan")


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    report_case_id = Column(Integer, ForeignKey("report_cases.id"), nullable=False)
    panel = Column(String(120), nullable=False)
    test_name = Column(String(120), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    status = Column(String(30), nullable=True)
    reference_low = Column(Float, nullable=True)
    reference_high = Column(Float, nullable=True)
    critical_low = Column(Float, nullable=True)
    critical_high = Column(Float, nullable=True)
    evidence = Column(Text, nullable=True)

    report_case = relationship("ReportCase", back_populates="lab_results")


class ClinicalPatternResult(Base):
    __tablename__ = "clinical_pattern_results"

    id = Column(Integer, primary_key=True, index=True)
    report_case_id = Column(Integer, ForeignKey("report_cases.id"), nullable=False)
    pattern_code = Column(String(150), nullable=False)
    pattern_name = Column(String(200), nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=True)
    confidence_level = Column(String(30), nullable=True)
    evidence_for = Column(JSON, nullable=True)
    missing_evidence = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    report_case = relationship("ReportCase", back_populates="clinical_patterns")
    retrieved_sources = relationship("RetrievedSource", back_populates="clinical_pattern")


class RetrievedSource(Base):
    __tablename__ = "retrieved_sources"

    id = Column(Integer, primary_key=True, index=True)
    report_case_id = Column(Integer, ForeignKey("report_cases.id"), nullable=False)
    pattern_result_id = Column(Integer, ForeignKey("clinical_pattern_results.id"), nullable=True)
    source_id = Column(String(150), nullable=False)
    title = Column(String(250), nullable=False)
    snippet = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)

    report_case = relationship("ReportCase", back_populates="retrieved_sources")
    clinical_pattern = relationship("ClinicalPatternResult", back_populates="retrieved_sources")


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_case_id = Column(Integer, ForeignKey("report_cases.id"), nullable=False)
    report_markdown = Column(Text, nullable=False)
    report_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    report_case = relationship("ReportCase", back_populates="generated_reports")


class KnowledgeDocMetadata(Base):
    __tablename__ = "knowledge_docs_metadata"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(150), nullable=False, unique=True)
    title = Column(String(250), nullable=False)
    file_path = Column(String(500), nullable=False)
    panel = Column(String(120), nullable=True)
    chunk_count = Column(Integer, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    id = Column(Integer, primary_key=True, index=True)
    input_json = Column(JSON, nullable=False)
    expected_patterns = Column(JSON, nullable=False)
    difficulty = Column(String(50), nullable=True)
    panel = Column(String(120), nullable=True)
    lab_count = Column(Integer, nullable=True)
    symptom_count = Column(Integer, nullable=True)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    eval_case_id = Column(Integer, ForeignKey("evaluation_cases.id"), nullable=False)
    predicted_patterns = Column(JSON, nullable=True)
    expected_patterns = Column(JSON, nullable=True)
    is_top3_correct = Column(Boolean, default=False)
    latency_ms = Column(Float, nullable=True)
    run_id = Column(String(150), nullable=True)
