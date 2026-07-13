from datetime import datetime
from pathlib import Path

from app.api.routes import _safe_report_path
from app.services.report_generator_agent import REPORT_OUTPUT_DIR
from app.services.report_generator_agent import ReportGeneratorAgent
from app.services.report_generator_agent import format_clinician_datetime, report_timezone_label
from app.services.safety_agent import (
    SAFETY_NOTICE,
    ensure_safety_notice,
    sanitize_dashboard,
    sanitize_text,
)


def test_sanitize_text_rewrites_unsafe_language():
    text = "confirmed diagnosis: the patient has anemia. treatment plan: prescribe iron."

    sanitized = sanitize_text(text)

    assert "confirmed diagnosis" not in sanitized.lower()
    assert "the patient has" not in sanitized.lower()
    assert "treatment plan" not in sanitized.lower()
    assert "prescribe" not in sanitized.lower()
    assert "clinician review" in sanitized.lower()


def test_sanitize_text_rewrites_required_audit_phrases():
    text = (
        "diagnose condition. prescription needed. medication advice included. "
        "treatment recommendation follows."
    )

    sanitized = sanitize_text(text)
    lowered = sanitized.lower()

    for phrase in ["diagnose", "prescription", "medication advice", "treatment recommendation"]:
        assert phrase not in lowered
    assert "clinician review" in lowered or "clinician-directed" in lowered


def test_ensure_safety_notice_appends_when_missing():
    text = ensure_safety_notice("Findings may suggest review.")

    assert text.endswith(SAFETY_NOTICE)


def test_sanitize_dashboard_recursively_sanitizes_strings():
    dashboard = {
        "patient_summary": {"clinical_notes": "the patient has anemia"},
        "clinical_patterns": [{"warnings": ["confirmed diagnosis"]}],
    }

    sanitized = sanitize_dashboard(dashboard)

    assert sanitized["safety_notice"] == SAFETY_NOTICE
    assert "the patient has" not in sanitized["patient_summary"]["clinical_notes"].lower()
    assert "confirmed diagnosis" not in sanitized["clinical_patterns"][0]["warnings"][0].lower()


def _sample_dashboard(generator: ReportGeneratorAgent) -> dict:
    return generator.build_dashboard(
        case_data={
            "age": 50,
            "sex": "female",
            "selected_panel": "CBC_Panel",
            "symptoms": ["pale skin"],
            "clinical_notes": "Findings may suggest review.",
        },
        lab_results=[
            {
                "test_name": "Hemoglobin",
                "value": 5.0,
                "unit": "g/dL",
                "status": "Critical",
                "reference_low": 12.0,
                "reference_high": 16.0,
                "critical_low": 7.0,
                "critical_high": None,
                "evidence": "Requires clinician review.",
            }
        ],
        clinical_patterns=[
            {
                "rank": 1,
                "pattern_code": "anemia_pattern",
                "pattern_name": "Anemia review pattern",
                "score": 2.0,
                "confidence_level": "high",
                "evidence_for": ["Hemoglobin is Critical"],
                "missing_evidence": [],
                "warnings": ["Requires clinician review."],
            }
        ],
    )


def test_build_dashboard_emits_timezone_aware_generated_at():
    generator = ReportGeneratorAgent()
    dashboard = _sample_dashboard(generator)

    parsed = datetime.fromisoformat(dashboard["generated_at"])

    assert parsed.tzinfo is not None


def test_report_datetime_formats_utc_timestamp_in_amman_time(monkeypatch):
    monkeypatch.setenv("REPORT_TIMEZONE", "Asia/Amman")

    assert format_clinician_datetime("2026-07-12T11:44:19+00:00") == "12 Jul 2026 • 2:44 PM"
    assert report_timezone_label() == "Asia/Amman"


def test_report_generator_builds_markdown_html_and_saves(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = ReportGeneratorAgent()
    dashboard = _sample_dashboard(generator)

    markdown = generator.render_markdown(dashboard)
    html_report = generator.render_html(dashboard)
    report_path = generator.save_markdown_report(123, markdown)
    html_path = generator.save_html_report(123, html_report)
    pdf_path = generator.render_pdf({**dashboard, "report_case_id": 123}, tmp_path / "report.pdf")

    assert dashboard["safety_notice"] == SAFETY_NOTICE
    assert "# MedDx Clinical Review Report" in markdown
    assert "## Clinical Safety Notice" in markdown
    assert "## Case Overview" in markdown
    assert "## Review Summary" in markdown
    assert "## Laboratory Results" in markdown
    assert "## Clinical Interpretation Limitations" in markdown
    assert "## Technical Metadata" in markdown
    assert "## Final Safety Notice" in markdown
    assert "<style>" in html_report
    assert SAFETY_NOTICE in html_report
    assert "MedDx Assistant" in html_report
    assert Path(report_path).read_text(encoding="utf-8") == markdown
    assert Path(html_path).read_text(encoding="utf-8") == html_report
    assert report_path.endswith(".md")
    assert html_path.endswith(".html")
    pdf_bytes = Path(pdf_path).read_bytes()
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000
    assert b"For clinicians only" in pdf_bytes


def test_report_generator_uses_unique_file_names(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = ReportGeneratorAgent()

    first = generator.save_markdown_report(13, "first", generated_at="2026-07-10T19:13:11")
    second = generator.save_markdown_report(13, "second", generated_at="2026-07-10T19:13:11")

    assert first != second
    assert Path(first).name == "meddx_case_13_2026-07-10_191311.md"
    assert Path(second).name == "meddx_case_13_2026-07-10_191311_2.md"


def test_report_paths_keep_pdf_unique_with_matching_basename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = ReportGeneratorAgent()

    markdown, html = generator.build_report_paths(17, "2026-07-10T19:54:09")
    pdf = generator.pdf_path_from_markdown_path(markdown)
    Path(pdf).parent.mkdir(parents=True, exist_ok=True)
    Path(pdf).write_bytes(b"%PDF-existing")
    next_markdown, next_html = generator.build_report_paths(17, "2026-07-10T19:54:09")

    assert Path(markdown).stem == Path(html).stem == Path(pdf).stem
    assert Path(markdown).name == "meddx_case_17_2026-07-10_195409.md"
    assert next_markdown != markdown
    assert Path(next_markdown).stem == Path(next_html).stem


def test_pdf_handles_long_multi_page_content_and_empty_states(tmp_path):
    generator = ReportGeneratorAgent()
    dashboard = generator.build_dashboard(
        case_data={"age": 40, "sex": "male", "selected_panel": "CBC_Panel", "symptoms": [], "clinical_notes": "the patient has findings for review"},
        lab_results=[
            {
                "test_name": f"Lab {index}", "value": index, "unit": "unit", "status": "Normal",
                "reference_low": 0, "reference_high": 10, "critical_low": None, "critical_high": None,
                "evidence": "Long evidence requiring safe wrapping. " * 30,
            }
            for index in range(20)
        ],
        clinical_patterns=[], retrieved_sources=[], clinical_warnings=[], missing_required_labs=[],
    )
    dashboard["report_case_id"] = 45
    pdf_path = generator.render_pdf(dashboard, tmp_path / "long-report.pdf")
    pdf_bytes = Path(pdf_path).read_bytes()

    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_bytes.count(b"/Type /Page") >= 3
    assert b"For clinicians only" in pdf_bytes
    assert b"the patient has" not in pdf_bytes.lower()
    assert b"No abnormal findings" in pdf_bytes
    assert b"No retrieved evidence sources" in pdf_bytes


def test_report_content_handles_empty_states_and_avoids_forbidden_phrases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = ReportGeneratorAgent()
    dashboard = generator.build_dashboard(
        case_data={"age": 40, "sex": "male", "selected_panel": "CBC_Panel", "symptoms": [], "clinical_notes": None},
        lab_results=[],
        clinical_patterns=[],
        retrieved_sources=[],
        clinical_warnings=[],
        missing_required_labs=[],
    )

    markdown = generator.render_markdown(dashboard)
    html_report = generator.render_html(dashboard)
    combined = f"{markdown}\n{html_report}".lower()

    assert "no retrieved evidence sources were available for this review" in combined
    assert "no abnormal findings were identified" in combined
    for phrase in ["confirmed diagnosis", "the patient has", "diagnosed with", "definitely", "prescribe", "start medication", "stop medication", "treatment plan"]:
        assert phrase not in combined


def test_panel_labels_render_as_human_readable(tmp_path):
    generator = ReportGeneratorAgent()
    dashboard = _sample_dashboard(generator)
    dashboard["patient_summary"]["selected_panel"] = "Diabetic_Panel"
    dashboard["severity"] = {"label": "Urgent", "confidence": 0.85, "source": "fine_tuned_model"}

    markdown = generator.render_markdown(dashboard)
    html_report = generator.render_html(dashboard)
    pdf_path = generator.render_pdf({**dashboard, "report_case_id": 123}, tmp_path / "report.pdf")

    assert "Diabetic / Rapid Glucose Panel" in markdown
    assert "Diabetic / Rapid Glucose Panel" in html_report
    assert b"Diabetic_Panel" not in Path(pdf_path).read_bytes()


def test_review_summary_includes_severity_and_not_available_card_is_removed(tmp_path):
    generator = ReportGeneratorAgent()
    dashboard = _sample_dashboard(generator)
    dashboard["severity"] = {"label": "Urgent", "confidence": 0.85, "source": "fine_tuned_model"}

    markdown = generator.render_markdown(dashboard)
    html_report = generator.render_html(dashboard)
    summary_section = markdown.split("## Review Summary", 1)[1].split("## Laboratory Results", 1)[0]

    assert "Severity label" in markdown
    assert "Confidence" in markdown
    assert "Not available" not in summary_section
    assert "<small>Not available</small>" not in html_report


def test_pattern_metadata_starts_on_separate_lines_and_sources_are_well_formatted(tmp_path):
    generator = ReportGeneratorAgent()
    dashboard = _sample_dashboard(generator)
    dashboard["clinical_patterns"] = [
        {
            "rank": 1,
            "pattern_code": "anemia_pattern",
            "pattern_name": "Elevated glucose or HbA1c supporting a hyperglycemia review pattern",
            "score": 4.0,
            "confidence_level": "moderate",
            "evidence_for": ["Elevated glucose"],
            "missing_evidence": [],
            "warnings": [],
            "retrieved_sources": [],
        }
    ]
    dashboard["retrieved_sources"] = [
        {"source_id": "doc-1", "title": "Diabetic Rapid Glucose Interpretation", "snippet": "High glucose supports review", "similarity_score": 0.91, "pattern_code": "anemia_pattern"},
        {"source_id": "doc-1", "title": "Diabetic Rapid Glucose Interpretation", "snippet": "High glucose supports review", "similarity_score": 0.97, "pattern_code": "anemia_pattern"},
        {"source_id": "doc-2", "title": "Clinical Context", "snippet": "Different section with distinct findings", "similarity_score": 0.88, "pattern_code": "anemia_pattern"},
    ]

    dashboard = generator.build_dashboard(
        case_data=dashboard["patient_summary"],
        lab_results=dashboard["lab_results"],
        clinical_patterns=dashboard["clinical_patterns"],
        retrieved_sources=dashboard["retrieved_sources"],
        clinical_warnings=dashboard["clinical_warnings"],
        missing_required_labs=dashboard["missing_required_labs"],
        generated_at=dashboard["generated_at"],
    )
    markdown = generator.render_markdown(dashboard)

    assert "- Rank: 1" in markdown
    assert "- Confidence: moderate" in markdown
    assert "- Score: 4.0" in markdown
    assert "- Retrieved Sources: 2" in markdown
    assert "- Relevant Finding:" in markdown
    assert "- Clinical Context:" in markdown
    assert "- Similarity Score:" in markdown
    assert "- Source ID:" in markdown
    assert len(dashboard["retrieved_sources"]) == 2


def test_safe_report_path_blocks_path_traversal():
    safe_path = REPORT_OUTPUT_DIR / "meddx_case_1_2026-07-10_191311.md"

    assert _safe_report_path(str(safe_path), ".md") is not None
    assert _safe_report_path("../../etc/passwd", ".md") is None
