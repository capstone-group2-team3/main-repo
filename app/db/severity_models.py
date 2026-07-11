from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class CaseSeverity(Base):
    __tablename__ = "case_severity"

    id = Column(Integer, primary_key=True, index=True)
    report_case_id = Column(Integer, ForeignKey("report_cases.id"), nullable=False, unique=True)
    severity_label = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report_case = relationship("ReportCase", back_populates="case_severity")
