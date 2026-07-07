from typing import Any

from pydantic import BaseModel, Field


class LabInput(BaseModel):
    name: str
    value: float
    unit: str | None = None


class ReportRequest(BaseModel):
    age: int
    sex: str
    selected_panel: str
    symptoms: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None
    labs: list[LabInput] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str


class PlaceholderAnalyzeResponse(BaseModel):
    message: str
    report_case_id: int
    received: dict[str, Any]
    safety_notice: str
