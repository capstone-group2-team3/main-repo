from pathlib import Path

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import routes as api_routes
from app.db.database import Base
from app.db.models import ClinicalPatternResult, GeneratedReport, LabResult, ReportCase
from app.models.schemas import ReportRequest


class RouteResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = jsonable_encoder(payload)

    def json(self):
        return self._payload


class RouteClient:
    def __init__(self, db):
        self.db = db

    def _call(self, func, *args, **kwargs) -> RouteResponse:
        try:
            return RouteResponse(200, func(*args, **kwargs))
        except HTTPException as error:
            return RouteResponse(error.status_code, {"detail": error.detail})

    def get(self, path: str) -> RouteResponse:
        if path == "/health":
            return self._call(api_routes.health)

        if path == "/templates":
            return self._call(api_routes.get_templates)

        if path.startswith("/templates/"):
            return self._call(api_routes.get_template, path.removeprefix("/templates/"))

        if path.startswith("/cases/"):
            return self._call(api_routes.get_case, int(path.removeprefix("/cases/")), self.db)

        raise AssertionError(f"Unhandled test route: GET {path}")

    def post(self, path: str, json: dict) -> RouteResponse:
        if path != "/reports/analyze":
            raise AssertionError(f"Unhandled test route: POST {path}")

        try:
            payload = ReportRequest(**json)
        except ValidationError as error:
            return RouteResponse(422, {"detail": error.errors()})

        return self._call(api_routes.analyze_report, payload, self.db)


@pytest.fixture()
def test_db(tmp_path):
    """
    Create a temporary SQLite database for each test run.

    This keeps tests isolated and prevents pytest from writing into the real
    local database file at data/meddx.db.
    """
    db_path = tmp_path / "test_meddx.db"
    test_database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )

    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db):
    db = test_db()
    try:
        yield RouteClient(db)
    finally:
        db.close()


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_templates_endpoints_return_available_panels(client):
    response = client.get("/templates")
    data = response.json()

    assert response.status_code == 200
    assert any(panel["panel_name"] == "CBC_Panel" for panel in data["panels"])

    template_response = client.get("/templates/CBC_Panel")
    template = template_response.json()

    assert template_response.status_code == 200
    assert template["panel_name"] == "CBC_Panel"
    assert any(test["name"] == "Hemoglobin" for test in template["tests"])


def test_analyze_report_placeholder_returns_case_id_and_safety_notice(client):
    payload = {
        "age": 58,
        "sex": "male",
        "selected_panel": "Cardiac Enzymes Panel",
        "symptoms": ["chest pain", "shortness of breath", "sweating"],
        "clinical_notes": "Patient came to ER with chest pain.",
        "labs": [
            {"name": "Troponin", "value": 75, "unit": "ng/L"},
            {"name": "CPK", "value": 420, "unit": "U/L"},
        ],
    }

    response = client.post("/reports/analyze", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["report_case_id"] == 1
    assert data["received"]["age"] == 58
    assert data["received"]["selected_panel"] == "Cardiac Enzymes Panel"
    assert data["received"]["labs"][0]["name"] == "Troponin"
    assert data["safety_notice"] == "For clinicians only — supports review, not diagnosis or prescribing."
    assert "generated_at" in data
    assert data["report_file_path"].startswith("reports/generated_reports/meddx_case_1_")
    assert data["report_file_path"].endswith(".md")
    assert data["report_format_version"] == "1.0"
    assert data["report"]["generated"] is True
    assert data["report"]["markdown_download_url"] == "/reports/1/download/markdown"
    assert data["report"]["html_download_url"] == "/reports/1/download/html"
    assert data["report"]["html_path"].endswith(".html")


def test_analyze_report_saves_case_and_case_can_be_fetched(client):
    payload = {
        "age": 45,
        "sex": "female",
        "selected_panel": "CBC Panel",
        "symptoms": ["fatigue", "dizziness"],
        "clinical_notes": "Initial CBC review.",
        "labs": [
            {"name": "Hemoglobin", "value": 9.8, "unit": "g/dL"},
            {"name": "WBC", "value": 7.5, "unit": "10^9/L"},
        ],
    }

    analyze_response = client.post("/reports/analyze", json=payload)
    report_case_id = analyze_response.json()["report_case_id"]

    case_response = client.get(f"/cases/{report_case_id}")
    case_data = case_response.json()

    assert case_response.status_code == 200
    assert case_data["id"] == report_case_id
    assert case_data["age"] == 45
    assert case_data["sex"] == "female"
    assert case_data["selected_panel"] == "CBC Panel"
    assert case_data["symptoms"] == ["fatigue", "dizziness"]
    assert case_data["clinical_notes"] == "Initial CBC review."
    assert isinstance(case_data["created_at"], str)


def test_analyze_report_accepts_name_aliases_persists_and_encodes(client, test_db):
    payload = {
        "age": 58,
        "sex": "male",
        "selected_panel": "Cardiac Enzymes Panel",
        "symptoms": ["chest pain", "shortness of breath"],
        "clinical_notes": "Alias normalization and persistence check.",
        "labs": [
            {"name": "TnI", "value": 75, "unit": "ng/L"},
            {"name": "CK", "value": 420, "unit": "U/L"},
        ],
    }

    response = client.post("/reports/analyze", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["received"]["labs"][0]["name"] == "TnI"
    assert [lab["test_name"] for lab in data["lab_results"]] == ["Troponin", "CPK"]
    assert data["lab_results"][0]["status"] == "Critical"
    assert data["lab_results"][1]["status"] == "High"
    assert data["report"]["pdf_path"].endswith(".pdf")
    assert data["report"]["pdf_download_url"] == f"/reports/{data['report_case_id']}/download/pdf"
    assert Path(data["report"]["pdf_path"]).read_bytes().startswith(b"%PDF-")
    assert jsonable_encoder(data)

    db = test_db()
    try:
        assert db.query(ReportCase).count() == 1
        assert db.query(LabResult).count() == 2
        assert db.query(ClinicalPatternResult).count() >= 0
        assert db.query(GeneratedReport).count() == 1
    finally:
        db.close()


def test_analyze_report_persists_clinical_patterns_when_matched(client, test_db):
    payload = {
        "age": 45,
        "sex": "female",
        "selected_panel": "CBC Panel",
        "symptoms": ["fatigue"],
        "clinical_notes": "Pattern persistence check.",
        "labs": [
            {"name": "Hgb", "value": 9.8, "unit": "g/dL"},
            {"name": "WBC", "value": 7.5, "unit": "10^9/L"},
            {"name": "Platelets", "value": 200, "unit": "10^9/L"},
        ],
    }

    response = client.post("/reports/analyze", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["lab_results"][0]["test_name"] == "Hemoglobin"
    assert data["clinical_patterns"]
    assert data["clinical_patterns"][0]["pattern"] == "Low Hemoglobin levels indicating potential anemia."
    assert data["clinical_patterns"][0]["pattern_name"] == "Low Hemoglobin levels indicating potential anemia."
    assert "retrieved_sources" in data["clinical_patterns"][0]

    db = test_db()
    try:
        assert db.query(ClinicalPatternResult).count() == 1
    finally:
        db.close()


def test_analyze_report_rejects_invalid_payload(client):
    invalid_payload = {
        "age": "not-a-number",
        "sex": "male",
        "selected_panel": "Cardiac Enzymes Panel",
        "symptoms": ["chest pain"],
        "labs": [
            {"name": "Troponin", "value": 75, "unit": "ng/L"},
        ],
    }

    response = client.post("/reports/analyze", json=invalid_payload)

    assert response.status_code == 422


def test_report_download_endpoints_return_latest_files(client):
    payload = {
        "age": 50,
        "sex": "female",
        "selected_panel": "CBC Panel",
        "symptoms": ["fatigue"],
        "clinical_notes": "Download endpoint check.",
        "labs": [
            {"name": "Hemoglobin", "value": 9.8, "unit": "g/dL"},
            {"name": "WBC", "value": 7.5, "unit": "10^9/L"},
            {"name": "Platelets", "value": 200, "unit": "10^9/L"},
        ],
    }

    client.post("/reports/analyze", json=payload)

    markdown_response = api_routes.download_markdown_report(1, client.db)
    html_response = api_routes.download_html_report(1, client.db)
    pdf_response = api_routes.download_pdf_report(1, client.db)

    assert isinstance(markdown_response, FileResponse)
    assert isinstance(html_response, FileResponse)
    assert markdown_response.media_type == "text/markdown"
    assert html_response.media_type == "text/html"
    assert isinstance(pdf_response, FileResponse)
    assert pdf_response.media_type == "application/pdf"


def test_report_download_invalid_case_id_returns_404(client):
    response = client._call(api_routes.download_markdown_report, 9999, client.db)

    assert response.status_code == 404
    assert "No generated report found" in response.json()["detail"]


def test_pdf_download_missing_case_and_path_traversal_return_404(client):
    missing = client._call(api_routes.download_pdf_report, 9999, client.db)
    assert missing.status_code == 404

    assert api_routes._safe_report_path("../../etc/passwd", ".pdf") is None
