from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base 

class CaseSeverity(Base):
    __tablename__ = "case_severity"

    id = Column(Integer, primary_key=True, index=True)
    report_case_id = Column(Integer)
    severity_label = Column(String)
    confidence = Column(Float)
    source = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())