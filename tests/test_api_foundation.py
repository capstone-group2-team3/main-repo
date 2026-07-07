import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app


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

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db):
    return TestClient(app)


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
    assert "safety_notice" in data
    assert "does not provide a final diagnosis" in data["safety_notice"]


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
