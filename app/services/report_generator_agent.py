import html
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.safety_agent import (
    SAFETY_NOTICE,
    ensure_safety_notice,
    sanitize_dashboard,
    sanitize_text,
)


REPORT_FORMAT_VERSION = "1.0"
REPORT_OUTPUT_DIR = Path("reports/generated_reports")
DEFAULT_REPORT_TIMEZONE = "Asia/Amman"
SEVERITY_DISCLAIMER = (
    "This is a supportive prioritization signal only and does not replace clinician judgment."
)


def normalize_terminal_punctuation(text: Any, ensure_period: bool = False) -> str:
    value = str(text or "").strip()
    if not value:
        return value
    value = re.sub(r"([.!?])[.!?]+$", r"\1", value)
    if ensure_period and value[-1] not in ".!?":
        value += "."
    return value


def report_timezone_name() -> str:
    return os.getenv("REPORT_TIMEZONE", DEFAULT_REPORT_TIMEZONE).strip() or DEFAULT_REPORT_TIMEZONE


def report_timezone() -> ZoneInfo | timezone:
    try:
        return ZoneInfo(report_timezone_name())
    except ZoneInfoNotFoundError:
        return timezone.utc


def report_timezone_label() -> str:
    zone = report_timezone()
    return getattr(zone, "key", "UTC")


def format_clinician_datetime(value: Any) -> str:
    if not value:
        return "Not available"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return "Not available"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    local_time = parsed.astimezone(report_timezone())
    formatted = local_time.strftime("%d %b %Y • %I:%M %p")
    return formatted.replace("• 0", "• ")


class ReportGeneratorAgent:
    def build_dashboard(
        self,
        case_data: dict[str, Any],
        lab_results: list[dict[str, Any]],
        clinical_patterns: list[dict[str, Any]],
        retrieved_sources: list[dict[str, Any]] | None = None,
        clinical_warnings: list[Any] | None = None,
        missing_required_labs: list[str] | None = None,
        generated_at: str | None = None,
    ) -> dict[str, Any]:
        sources = self._deduplicate_sources(retrieved_sources or [])
        source_map = self._sources_by_pattern(sources)
        if generated_at is None:
            generated_at = datetime.now(timezone.utc).isoformat()

        dashboard = {
            "patient_summary": {
                "age": case_data.get("age"),
                "sex": case_data.get("sex"),
                "selected_panel": case_data.get("selected_panel"),
                "symptoms": case_data.get("symptoms", []),
                "clinical_notes": case_data.get("clinical_notes"),
            },
            "lab_results": [self._lab_result(lab) for lab in lab_results],
            "abnormal_findings": [
                self._abnormal_finding(lab)
                for lab in lab_results
                if lab.get("status") != "Normal"
            ],
            "clinical_warnings": [self._clinical_warning(warning) for warning in clinical_warnings or []],
            "clinical_patterns": [
                self._clinical_pattern(pattern, source_map)
                for pattern in clinical_patterns[:3]
            ],
            "retrieved_sources": [self._retrieved_source(source) for source in sources],
            "missing_required_labs": missing_required_labs or [],
            "safety_notice": SAFETY_NOTICE,
            "generated_at": generated_at,
            "report_format_version": REPORT_FORMAT_VERSION,
        }

        return dashboard

    def render_markdown(self, dashboard_json: dict[str, Any]) -> str:
        patient = dashboard_json.get("patient_summary", {})
        lab_results = dashboard_json.get("lab_results", [])
        abnormal_findings = dashboard_json.get("abnormal_findings", [])
        warnings = dashboard_json.get("clinical_warnings", [])
        patterns = dashboard_json.get("clinical_patterns", [])
        retrieved_sources = dashboard_json.get("retrieved_sources", [])
        missing_required_labs = dashboard_json.get("missing_required_labs", [])
        severity = dashboard_json.get("severity")
        summary = self._review_summary(dashboard_json)
        case_id = self._display(dashboard_json.get("report_case_id") or dashboard_json.get("case_id"))
        generated_at_raw = dashboard_json.get("generated_at")
        generated_at = format_clinician_datetime(generated_at_raw)
        generated_timezone = report_timezone_label()

        lines = [
            "# MedDx Clinical Review Report",
            "",
            "## Clinical Safety Notice",
            f"> {SAFETY_NOTICE}",
            "",
        ]

        if isinstance(severity, dict):
            lines.extend(
                [
                    "## Severity Support Alert",
                    f"- Severity label: {self._display(severity.get('label'))}",
                    f"- Confidence: {self._format_confidence(severity.get('confidence'))}",
                    f"- Source: {self._source_label(severity.get('source'))}",
                    f"> {SEVERITY_DISCLAIMER}",
                    "",
                ]
            )

        selected_panel_label = self._format_panel_label(patient.get("selected_panel"))
        lines.extend(
            [
            "## Case Overview",
            f"- Case ID: {case_id}",
            f"- Generated date/time: {generated_at}",
            f"- Display timezone: {generated_timezone}",
            f"- Selected panel: {selected_panel_label}",
            f"- Patient age: {self._display(patient.get('age'))}",
            f"- Patient sex: {self._display(patient.get('sex'))}",
            f"- Symptoms: {self._join(patient.get('symptoms', []))}",
            f"- Clinical notes: {self._display(patient.get('clinical_notes'))}",
            "",
            "## Review Summary",
            ]
        )

        if isinstance(severity, dict):
            lines.append(f"- Severity label: {self._display(severity.get('label'))}")
            lines.append(f"- Confidence: {self._format_confidence(severity.get('confidence'))}")
            lines.append(f"- Severity source: {self._source_label(severity.get('source'))}")

        for label, value in summary.items():
            if label in {"Total labs reviewed", "Total abnormal findings", "Total clinical patterns", "Total retrieved sources"}:
                lines.append(f"- {label}: {value}")

        lines.extend(
            [
                "",
                "## Laboratory Results",
                "",
                "| Test | Value | Unit | Reference Range | Status | Evidence |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )

        if lab_results:
            for lab in lab_results:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._md_cell(lab.get("test_name")),
                            self._md_cell(lab.get("value")),
                            self._md_cell(lab.get("unit")),
                            self._md_cell(self._range_text(lab)),
                            self._md_cell(lab.get("status")),
                            self._md_cell(lab.get("evidence")),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("| Not available | Not available | Not available | Not available | Unknown | No lab results were returned. |")

        lines.extend(["", "## Abnormal Findings Requiring Clinician Review"])
        if abnormal_findings:
            for finding in abnormal_findings:
                lines.extend(
                    [
                        f"### {self._display(finding.get('test_name'))}",
                        f"- Value: {self._display(finding.get('value'))} {self._display(finding.get('unit'))}",
                        f"- Status: {self._display(finding.get('status'))}",
                        f"- Reference range: {self._range_text(finding)}",
                        f"- Evidence: {self._display(finding.get('evidence'))}",
                    ]
                )
        else:
            lines.append("No abnormal findings were identified using the configured educational reference ranges.")

        lines.extend(["", "## Clinical Warnings"])
        if warnings:
            for warning in warnings:
                lines.append(
                    f"- Severity: {self._display(warning.get('severity', 'Review'))}; "
                    f"Associated item: {self._display(warning.get('associated_item'))}; "
                    f"{self._display(warning.get('text'))}"
                )
        else:
            lines.append("No clinical warnings were returned for this review.")

        lines.extend(["", "## Top Clinical Patterns"])
        if patterns:
            for pattern in patterns:
                lines.extend(
                    [
                        f"### Rank {self._display(pattern.get('rank'))}: {normalize_terminal_punctuation(self._display(pattern.get('pattern_name')))}",
                        "This pattern may be consistent with the submitted findings and requires clinician review.",
                        f"- Rank: {self._display(pattern.get('rank'))}",
                        f"- Confidence: {self._display(pattern.get('confidence_level'))}",
                        f"- Score: {self._display(pattern.get('score'))}",
                        f"- Retrieved Sources: {len(pattern.get('retrieved_sources', []))}",
                    ]
                )
        else:
            lines.append("No top clinical patterns were returned for this review.")

        lines.extend(["", "## Missing Required Labs"])
        if missing_required_labs:
            for lab_name in missing_required_labs:
                lines.append(f"- {self._display(lab_name)}")
            lines.append("Interpretation may be limited until missing information is reviewed.")
        else:
            lines.append("No missing required labs were reported for the selected panel.")

        lines.extend(["", "## Retrieved Evidence Sources"])
        if retrieved_sources:
            for source in retrieved_sources:
                lines.extend(
                    [
                        f"### {self._display(source.get('title'))}",
                        f"- Relevant Finding: {self._display(source.get('snippet'))}",
                        f"- Clinical Context: {self._display(source.get('pattern_code'))}",
                        f"- Similarity Score: {self._format_score(source.get('similarity_score'))}",
                        f"- Source ID: {self._display(source.get('source_id'))}",
                    ]
                )
        else:
            lines.append("No retrieved evidence sources were available for this review.")

        lines.extend(
            [
                "",
                "## Clinical Interpretation Limitations",
                "- Configured ranges are educational.",
                "- Ranges may differ by lab, age, sex, method, and clinical context.",
                "- This output supports review and does not replace clinician judgment.",
                "- This output is not a final diagnosis.",
                "- No medication or treatment recommendation is provided.",
                "",
                "## Technical Metadata",
                f"- Case ID: {case_id}",
                f"- Selected panel: {self._display(patient.get('selected_panel'))}",
                f"- Report generation timestamp: {self._display(generated_at_raw)}",
                f"- Report display timezone: {generated_timezone}",
                "- Application name: MedDx Assistant",
                f"- Report format version: {REPORT_FORMAT_VERSION}",
                f"- Backend-generated report path: {self._display(dashboard_json.get('report_file_path'))}",
                "",
                "## Final Safety Notice",
                f"> {SAFETY_NOTICE}",
            ]
        )

        return ensure_safety_notice(sanitize_text("\n".join(lines)))

    def render_html(self, dashboard_json: dict[str, Any]) -> str:
        patient = dashboard_json.get("patient_summary", {})
        lab_results = dashboard_json.get("lab_results", [])
        abnormal_findings = dashboard_json.get("abnormal_findings", [])
        warnings = dashboard_json.get("clinical_warnings", [])
        patterns = dashboard_json.get("clinical_patterns", [])
        retrieved_sources = dashboard_json.get("retrieved_sources", [])
        missing_required_labs = dashboard_json.get("missing_required_labs", [])
        severity = dashboard_json.get("severity")
        summary = self._review_summary(dashboard_json)
        case_id = self._display(dashboard_json.get("report_case_id") or dashboard_json.get("case_id"))
        generated_at = format_clinician_datetime(dashboard_json.get("generated_at"))
        generated_timezone = report_timezone_label()

        html_report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MedDx Clinical Review Report - Case {self._esc(case_id)}</title>
  <style>
    :root {{ color: #0f172a; background: #ffffff; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 48px; }}
    header {{ border-bottom: 4px solid #0f766e; background: #0f172a; color: white; padding: 28px; border-radius: 0 0 8px 8px; }}
    h1, h2, h3 {{ color: #0f172a; margin: 0; }}
    header h1 {{ color: white; font-size: 30px; }}
    header p {{ color: #cbd5e1; margin: 8px 0 0; }}
    section {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 22px; margin-top: 18px; break-inside: avoid; }}
    h2 {{ border-bottom: 1px solid #ccfbf1; padding-bottom: 10px; margin-bottom: 16px; font-size: 20px; }}
    .notice {{ background: #ecfeff; border-color: #99f6e4; color: #134e4a; font-weight: 700; }}
    .severity {{ border-width: 2px; }}
    .severity.routine {{ background: #f0fdf4; border-color: #86efac; color: #14532d; }}
    .severity.urgent {{ background: #fffbeb; border-color: #f59e0b; color: #78350f; }}
    .severity.critical {{ background: #fef2f2; border-color: #ef4444; color: #7f1d1d; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; background: #f8fafc; }}
    .card small {{ display: block; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }}
    .card strong {{ display: block; margin-top: 6px; font-size: 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    thead {{ background: #f1f5f9; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ color: #0f172a; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 4px 9px; font-size: 12px; font-weight: 800; }}
    .normal {{ background: #dcfce7; color: #166534; }}
    .low, .high {{ background: #fef3c7; color: #92400e; }}
    .critical {{ background: #fee2e2; color: #991b1b; }}
    .unknown {{ background: #e2e8f0; color: #475569; }}
    .teal {{ color: #0f766e; }}
    .muted {{ color: #64748b; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 6px 0; }}
    footer {{ margin-top: 24px; padding: 18px; color: #134e4a; background: #ecfeff; border: 1px solid #99f6e4; border-radius: 8px; font-weight: 700; }}
    @media print {{
      body {{ background: white; font-size: 12px; }}
      main {{ max-width: none; padding: 0; }}
      header, section, footer {{ border-radius: 0; box-shadow: none; }}
      section, .card {{ break-inside: avoid; page-break-inside: avoid; }}
      thead {{ display: table-header-group; }}
      a, button, .interactive-only {{ display: none !important; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>MedDx Assistant</h1>
    <p>Clinical Review Report • Case {self._esc(case_id)} • Generated {self._esc(generated_at)} • {self._esc(generated_timezone)}</p>
  </header>
  <section class="notice">{self._esc(SAFETY_NOTICE)}</section>
  {self._html_severity(severity)}
  {self._html_case_overview(case_id, generated_at, generated_timezone, patient)}
  {self._html_summary(summary)}
  {self._html_lab_results(lab_results)}
  {self._html_abnormal_findings(abnormal_findings)}
  {self._html_warnings(warnings)}
  {self._html_patterns(patterns)}
  {self._html_missing_labs(missing_required_labs)}
  {self._html_sources(retrieved_sources)}
  {self._html_limitations()}
  <footer>{self._esc(SAFETY_NOTICE)}</footer>
</main>
</body>
</html>"""

        return sanitize_text(html_report)

    def render_pdf(self, dashboard_json: dict[str, Any], output_path: str | Path) -> str:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        dashboard = sanitize_dashboard(dashboard_json)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        styles = getSampleStyleSheet()
        navy = colors.HexColor("#0F172A")
        teal = colors.HexColor("#0F766E")
        pale_teal = colors.HexColor("#ECFEFF")
        border = colors.HexColor("#CBD5E1")
        muted = colors.HexColor("#475569")
        subtle_gray = colors.HexColor("#F8FAFC")
        light_warn = colors.HexColor("#FEF2F2")
        styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=navy, spaceAfter=2 * mm))
        styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=12, textColor=muted, spaceAfter=4 * mm))
        styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=navy, spaceBefore=5 * mm, spaceAfter=2.2 * mm))
        styles.add(ParagraphStyle(name="BodySafe", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=muted, spaceAfter=1.3 * mm))
        styles.add(ParagraphStyle(name="SmallSafe", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9.5, textColor=muted))
        styles.add(ParagraphStyle(name="Notice", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.8, leading=11.5, textColor=colors.HexColor("#134E4A"), alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="MetricValue", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=12.5, leading=14, textColor=navy, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="MetricLabel", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9.5, textColor=muted, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="CardTitle", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9.2, leading=12, textColor=navy, spaceAfter=1.2 * mm))
        styles.add(ParagraphStyle(name="CardBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10.2, textColor=muted))
        styles.add(ParagraphStyle(name="Label", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.8, leading=10.2, textColor=navy, spaceAfter=0.6 * mm))
        styles.add(ParagraphStyle(name="Badge", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=navy, alignment=TA_CENTER))

        def safe(value: Any) -> str:
            if value is None or value == "":
                return "Not available"
            return html.escape(sanitize_text(str(value)))

        def paragraph(value: Any, style: str = "BodySafe"):
            return Paragraph(safe(value), styles[style])

        def section(title: str) -> list[Any]:
            return [Paragraph(safe(title), styles["SectionTitle"])]

        def bullet(label: str, value: Any) -> Paragraph:
            return Paragraph(f"<b>{safe(label)}:</b> {safe(value)}", styles["BodySafe"])

        def metric_card(label: str, value: Any) -> Table:
            return Table(
                [[Paragraph(f"<b>{safe(value)}</b>", styles["MetricValue"])], [Paragraph(safe(label), styles["MetricLabel"])]],
                colWidths=[(A4[0] - 42 * mm) / 4],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.6, border),
                    ("BACKGROUND", (0, 0), (-1, -1), subtle_gray),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
                ]),
            )

        def status_badge(status: Any) -> Paragraph:
            label = str(status or "Unknown")
            return Paragraph(f"<b>{safe(label)}</b>", styles["Badge"])

        def source_card(source: dict[str, Any]) -> KeepTogether:
            relevant, context = self._pdf_source_sections(source)
            title = safe(source.get("title"))
            body_parts = [
                f"<b>{title}</b>",
                "",
                f"<b>Relevant Finding</b>",
            ]
            body_parts.extend(f"• {safe(item)}<br/>" for item in relevant)
            body_parts.extend(["", f"<b>Clinical Context</b>"])
            body_parts.extend(f"• {safe(item)}<br/>" for item in context)
            body_parts.extend(["", f"<b>Source ID</b><br/>{safe(source.get('source_id'))}"])
            return KeepTogether(
                Table(
                    [[Paragraph("".join(body_parts), styles["CardBody"])]],
                    colWidths=[A4[0] - 40 * mm],
                    style=TableStyle([
                        ("BOX", (0, 0), (-1, -1), 0.6, border),
                        ("BACKGROUND", (0, 0), (-1, -1), subtle_gray),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
                    ]),
                )
            )

        def pattern_card(pattern: dict[str, Any]) -> KeepTogether:
            pattern_name = safe(normalize_terminal_punctuation(pattern.get("pattern_name"), ensure_period=True))
            rank = safe(pattern.get("rank"))
            confidence = safe(pattern.get("confidence_level"))
            score = pattern.get("score")
            evidence_for = [self._display(item) for item in pattern.get("evidence_for", []) if self._display(item) != "Not available"]
            score_text = f"<b>Score:</b> {safe(score)}<br/>" if score is not None and str(score).strip() not in {"", "None", "Not available"} else ""
            evidence_text = "<br/>".join(f"• {safe(item)}" for item in evidence_for) if evidence_for else "• Not available"
            body_parts = [
                f"<b>{pattern_name}</b>",
                "",
                f"<b>Rank:</b> {rank}<br/>",
                f"<b>Confidence:</b> {confidence}<br/>",
                score_text,
                f"<b>Retrieved Sources:</b> {len(pattern.get('retrieved_sources', []))}<br/>",
                f"<b>Evidence:</b><br/>{evidence_text}",
            ]
            return KeepTogether(
                Table(
                    [[Paragraph("".join(body_parts), styles["CardBody"])]],
                    colWidths=[A4[0] - 40 * mm],
                    style=TableStyle([
                        ("BOX", (0, 0), (-1, -1), 0.6, border),
                        ("BACKGROUND", (0, 0), (-1, -1), pale_teal),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
                    ]),
                )
            )

        def footer(canvas, document) -> None:
            canvas.saveState()
            canvas.setStrokeColor(border)
            canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.setFillColor(navy)
            canvas.drawString(18 * mm, 10 * mm, "MedDx Assistant")
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(muted)
            canvas.drawString(18 * mm, 7 * mm, "Clinical Review Report")
            canvas.drawString(18 * mm, 4 * mm, f"Case ID: {safe(case_id)}")
            canvas.drawString(96 * mm, 7 * mm, f"Generated: {format_clinician_datetime(dashboard.get('generated_at'))} {report_timezone_label()}")
            canvas.drawRightString(A4[0] - 18 * mm, 7 * mm, f"Page {document.page}")
            canvas.restoreState()

        document = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=24 * mm,
            title="MedDx Clinical Review Report",
            author="MedDx Assistant",
            pageCompression=0,
        )
        patient = dashboard.get("patient_summary", {})
        case_id = dashboard.get("report_case_id") or dashboard.get("case_id")
        summary = self._review_summary(dashboard)
        summary_items = [
            ("Total Labs Reviewed", summary.get("Total labs reviewed", 0)),
            ("Normal Findings", summary.get("Normal findings count", 0)),
            ("Abnormal Findings", summary.get("Total abnormal findings", 0)),
            ("Clinical Warnings", summary.get("Total clinical warnings", 0)),
            ("Clinical Patterns", summary.get("Total clinical patterns", 0)),
            ("Retrieved Sources", summary.get("Total retrieved sources", 0)),
            ("Missing Required Labs", summary.get("Missing required labs count", 0)),
        ]

        story: list[Any] = [
            Paragraph("MedDx Assistant", styles["ReportTitle"]),
            Paragraph("Clinical Review Report", styles["Heading1"]),
            Paragraph("Clinician-facing educational review dashboard", styles["ReportSubtitle"]),
            Spacer(1, 1 * mm),
            Table(
                [[Paragraph("Clinical Safety Notice", styles["SectionTitle"])], [Paragraph(safe(SAFETY_NOTICE), styles["Notice"])]],
                colWidths=[A4[0] - 36 * mm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), pale_teal),
                    ("BOX", (0, 0), (-1, -1), 0.8, teal),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]),
            ),
        ]

        severity = dashboard.get("severity")
        if isinstance(severity, dict):
            story.append(
                Table(
                    [
                        [Paragraph("Severity Support Alert", styles["SectionTitle"])],
                        [
                            Paragraph(
                                f"<b>Severity label:</b> {safe(severity.get('label'))}<br/>"
                                f"<b>Confidence:</b> {safe(self._format_confidence(severity.get('confidence')))}<br/>"
                                f"<b>Source:</b> {safe(self._source_label(severity.get('source')))}<br/>"
                                f"{safe(SEVERITY_DISCLAIMER)}",
                                styles["Notice"],
                            )
                        ],
                    ],
                    colWidths=[A4[0] - 36 * mm],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
                        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#F59E0B")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]),
                )
            )

        story.extend(section("Case Overview"))
        story.extend([
            bullet("Case ID", case_id),
            bullet("Generated", format_clinician_datetime(dashboard.get("generated_at"))),
            bullet("Display timezone", report_timezone_label()),
            bullet("Selected panel", self._format_panel_label(patient.get("selected_panel"))),
            bullet("Age", patient.get("age")),
            bullet("Sex", patient.get("sex")),
            bullet("Symptoms", ", ".join(patient.get("symptoms", [])) or None),
            bullet("Clinical notes", patient.get("clinical_notes")),
        ])

        story.extend(section("Review Summary"))
        summary_rows: list[list[Any]] = []
        for index in range(0, len(summary_items), 4):
            row = summary_items[index:index + 4]
            while len(row) < 4:
                row = [*row, ("", "")]
            summary_rows.append([metric_card(label, value) for label, value in row])
        story.append(KeepTogether(Table(summary_rows, colWidths=[(A4[0] - 42 * mm) / 4] * 4, style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
        ]))))
        story.append(Spacer(1, 2 * mm))
        story.append(PageBreak())

        story.extend(section("Laboratory Results"))
        labs = dashboard.get("lab_results", [])
        if labs:
            data_rows = []
            for lab in labs:
                status = str(lab.get("status") or "Unknown")
                status_value = Paragraph(f"<b>{safe(status)}</b>", styles["Badge"])
                data_rows.append([
                    paragraph(lab.get("test_name"), "SmallSafe"),
                    paragraph(lab.get("value"), "SmallSafe"),
                    paragraph(lab.get("unit"), "SmallSafe"),
                    paragraph(self._range_text(lab), "SmallSafe"),
                    status_value,
                    paragraph(lab.get("evidence"), "SmallSafe"),
                ])
        else:
            data_rows = []

        chunk_size = 8
        for chunk_index, start in enumerate(range(0, len(data_rows) or 1, chunk_size)):
            chunk_rows = [[paragraph(x, "SmallSafe") for x in ["Test", "Value", "Unit", "Reference range", "Status", "Evidence"]]]
            if data_rows:
                chunk_rows.extend(data_rows[start:start + chunk_size])
            else:
                chunk_rows.append([paragraph("Not available", "SmallSafe") for _ in range(6)])

            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, border),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
            for row_index in range(1, len(chunk_rows)):
                row_bg = colors.HexColor("#F8FAFC") if row_index % 2 else colors.white
                table_style.append(("BACKGROUND", (0, row_index), (-1, row_index), row_bg))
                status_key = str(labs[start + row_index - 1].get("status") or "Unknown").lower() if data_rows else "unknown"
                if status_key in {"low", "high", "critical"}:
                    table_style.append(("BACKGROUND", (0, row_index), (-1, row_index), light_warn))
                    table_style.append(("FONTNAME", (0, row_index), (-1, row_index), "Helvetica-Bold"))
                    table_style.append(("TEXTCOLOR", (0, row_index), (-1, row_index), navy))
            story.append(Table(chunk_rows, colWidths=[26 * mm, 15 * mm, 16 * mm, 24 * mm, 16 * mm, 49 * mm], repeatRows=1, splitByRow=1, style=TableStyle(table_style)))
            if len(data_rows) > chunk_size or chunk_index < (len(data_rows) - 1) // chunk_size or (not data_rows and chunk_index == 0):
                story.append(Spacer(1, 2 * mm))
                story.append(PageBreak())

        story.extend(section("Abnormal Findings"))
        if dashboard.get("abnormal_findings"):
            for finding in dashboard.get("abnormal_findings", []):
                story.append(Paragraph(f"<b>{safe(finding.get('test_name'))}</b>: {safe(finding.get('value'))} {safe(finding.get('unit'))} - {safe(finding.get('status'))}. {safe(finding.get('evidence'))}", styles["BodySafe"]))
        else:
            story.append(paragraph("No abnormal findings were identified using the configured educational reference ranges."))

        story.extend(section("Clinical Warnings"))
        if dashboard.get("clinical_warnings"):
            for warning in dashboard.get("clinical_warnings", []):
                story.append(Paragraph(f"<b>{safe(warning.get('severity', 'Review'))}</b>: {safe(warning.get('text'))}", styles["BodySafe"]))
        else:
            story.append(paragraph("No clinical warnings were returned for this review."))

        story.extend(section("Top Clinical Patterns"))
        if dashboard.get("clinical_patterns"):
            for pattern in dashboard.get("clinical_patterns", []):
                story.append(pattern_card(pattern))
        else:
            story.append(paragraph("No top clinical patterns were returned for this review."))

        story.extend(section("Missing Required Labs"))
        if dashboard.get("missing_required_labs"):
            story.append(Paragraph("<br/>".join(f"• {safe(lab)}" for lab in dashboard.get("missing_required_labs", [])), styles["BodySafe"]))
            story.append(paragraph("Interpretation may be limited until missing information is reviewed."))
        else:
            story.append(paragraph("No missing required labs were reported for the selected panel."))

        story.append(PageBreak())
        story.extend(section("Retrieved Evidence Sources"))
        if dashboard.get("retrieved_sources"):
            for source in dashboard.get("retrieved_sources", []):
                story.append(source_card(source))
                story.append(Spacer(1, 2 * mm))
        else:
            story.append(paragraph("No retrieved evidence sources were available for this review."))

        story.extend(section("Clinical Interpretation Limitations"))
        for limitation in [
            "Configured ranges are educational and may differ by laboratory, age, sex, method, and clinical context.",
            "This output supports review and does not replace clinician judgment.",
            "This output is not a final diagnosis.",
            "No medication or treatment recommendation is provided.",
        ]:
            story.append(Paragraph(f"• {safe(limitation)}", styles["BodySafe"]))
        story.extend([Spacer(1, 3 * mm), Paragraph("Final Safety Notice", styles["SectionTitle"]), Paragraph(safe(SAFETY_NOTICE), styles["Notice"])])

        document.build(story, onFirstPage=footer, onLaterPages=footer)
        return str(path)

    def save_markdown_report(
        self,
        case_id: int | str,
        markdown: str,
        generated_at: str | None = None,
        path: str | Path | None = None,
    ) -> str:
        report_path = Path(path) if path else self._report_path(case_id, "md", generated_at)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(markdown, encoding="utf-8")
        return str(report_path)

    def save_html_report(
        self,
        case_id: int | str,
        html_report: str,
        generated_at: str | None = None,
        path: str | Path | None = None,
    ) -> str:
        report_path = Path(path) if path else self._report_path(case_id, "html", generated_at)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(html_report, encoding="utf-8")
        return str(report_path)

    def build_report_paths(self, case_id: int | str, generated_at: str | None = None) -> tuple[str, str]:
        markdown_path = self._report_path(case_id, "md", generated_at)
        html_path = markdown_path.with_suffix(".html")
        counter = 2

        while markdown_path.exists() or html_path.exists() or markdown_path.with_suffix(".pdf").exists():
            timestamp = self._filename_timestamp(generated_at)
            safe_case_id = self._safe_filename_part(str(case_id))
            base = f"meddx_case_{safe_case_id}_{timestamp}_{counter}"
            markdown_path = REPORT_OUTPUT_DIR / f"{base}.md"
            html_path = REPORT_OUTPUT_DIR / f"{base}.html"
            counter += 1

        return str(markdown_path), str(html_path)

    def html_path_from_markdown_path(self, markdown_path: str | None) -> str | None:
        if not markdown_path:
            return None
        return str(Path(markdown_path).with_suffix(".html"))

    def pdf_path_from_markdown_path(self, markdown_path: str | None) -> str | None:
        if not markdown_path:
            return None
        return str(Path(markdown_path).with_suffix(".pdf"))

    def _report_path(self, case_id: int | str, suffix: str, generated_at: str | None) -> Path:
        REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = self._filename_timestamp(generated_at)
        safe_case_id = self._safe_filename_part(str(case_id))
        base = f"meddx_case_{safe_case_id}_{timestamp}"
        path = REPORT_OUTPUT_DIR / f"{base}.{suffix}"
        counter = 2

        while path.exists():
            path = REPORT_OUTPUT_DIR / f"{base}_{counter}.{suffix}"
            counter += 1

        return path

    def _filename_timestamp(self, generated_at: str | None) -> str:
        if generated_at:
            try:
                parsed = datetime.fromisoformat(generated_at)
            except ValueError:
                parsed = datetime.utcnow()
        else:
            parsed = datetime.utcnow()

        return parsed.strftime("%Y-%m-%d_%H%M%S")

    def _safe_filename_part(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_") or "unknown"

    def _review_summary(self, dashboard_json: dict[str, Any]) -> dict[str, int]:
        labs = dashboard_json.get("lab_results", [])
        statuses = [str(lab.get("status", "Unknown")).lower() for lab in labs if isinstance(lab, dict)]

        return {
            "Total labs reviewed": len(labs),
            "Normal findings count": statuses.count("normal"),
            "Low findings count": statuses.count("low"),
            "High findings count": statuses.count("high"),
            "Critical findings count": statuses.count("critical"),
            "Unknown findings count": statuses.count("unknown"),
            "Total abnormal findings": len(dashboard_json.get("abnormal_findings", [])),
            "Total clinical warnings": len(dashboard_json.get("clinical_warnings", [])),
            "Total clinical patterns": len(dashboard_json.get("clinical_patterns", [])),
            "Total retrieved sources": len(dashboard_json.get("retrieved_sources", [])),
            "Missing required labs count": len(dashboard_json.get("missing_required_labs", [])),
        }

    def _lab_result(self, lab: dict[str, Any]) -> dict[str, Any]:
        return {
            "test_name": lab.get("test_name"),
            "value": lab.get("value"),
            "unit": lab.get("unit"),
            "status": lab.get("status"),
            "reference_low": lab.get("reference_low"),
            "reference_high": lab.get("reference_high"),
            "critical_low": lab.get("critical_low"),
            "critical_high": lab.get("critical_high"),
            "evidence": lab.get("evidence"),
        }

    def _abnormal_finding(self, lab: dict[str, Any]) -> dict[str, Any]:
        return {
            "test_name": lab.get("test_name"),
            "value": lab.get("value"),
            "unit": lab.get("unit"),
            "status": lab.get("status"),
            "reference_low": lab.get("reference_low"),
            "reference_high": lab.get("reference_high"),
            "evidence": lab.get("evidence"),
        }

    def _clinical_warning(self, warning: Any) -> dict[str, Any]:
        if isinstance(warning, dict):
            return {
                "severity": warning.get("severity", "Review"),
                "text": warning.get("text") or warning.get("warning") or "Requires clinician review.",
                "associated_item": warning.get("associated_item") or warning.get("test") or warning.get("pattern"),
            }

        text = str(warning)
        severity = "Review"
        if "Critical" in text:
            severity = "Critical Review"
        elif "urgent" in text.lower():
            severity = "Urgent Review"

        return {"severity": severity, "text": text, "associated_item": None}

    def _clinical_pattern(
        self,
        pattern: dict[str, Any],
        source_map: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        pattern_code = pattern.get("pattern_code")

        return {
            "rank": pattern.get("rank"),
            "pattern_code": pattern_code,
            "pattern_name": pattern.get("pattern_name"),
            "score": pattern.get("score"),
            "confidence_level": pattern.get("confidence_level"),
            "evidence_for": pattern.get("evidence_for", []),
            "missing_evidence": pattern.get("missing_evidence", []),
            "warnings": pattern.get("warnings", []),
            "retrieved_sources": source_map.get(pattern_code, []),
        }

    def _retrieved_source(self, source: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_id": source.get("source_id"),
            "title": source.get("title"),
            "snippet": source.get("snippet"),
            "similarity_score": source.get("similarity_score"),
            "pattern_code": source.get("pattern_code"),
        }

    def _deduplicate_sources(self, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: dict[tuple[str, str, str], dict[str, Any]] = {}
        for source in sources:
            if not isinstance(source, dict):
                continue
            key = (
                self._display(source.get("source_id")),
                self._display(source.get("title")),
                self._display(source.get("snippet")),
            )
            current = seen.get(key)
            if current is None:
                seen[key] = self._retrieved_source(source)
                continue
            current_score = self._float_score(current.get("similarity_score"))
            incoming_score = self._float_score(source.get("similarity_score"))
            if incoming_score is not None and (current_score is None or incoming_score > current_score):
                seen[key] = self._retrieved_source(source)
        return list(seen.values())

    def _float_score(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _sources_by_pattern(self, sources: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        source_map: dict[str, list[dict[str, Any]]] = {}

        for source in sources:
            pattern_code = source.get("pattern_code")
            if pattern_code:
                source_map.setdefault(pattern_code, []).append(self._retrieved_source(source))

        return source_map

    def _pdf_source_sections(self, source: dict[str, Any]) -> tuple[list[str], list[str]]:
        relevant: list[str] = []
        context: list[str] = []

        title = self._display(source.get("title"))
        snippet = self._display(source.get("snippet"))
        pattern_code = self._display(source.get("pattern_code"))
        similarity = self._format_score(source.get("similarity_score"))

        if title != "Not available":
            relevant.append(title)
        if snippet != "Not available":
            relevant.append(snippet)
        if pattern_code != "Not available":
            context.append(f"Related pattern: {pattern_code}")
        if similarity != "Not available":
            context.append(f"Similarity score: {similarity}")

        if not relevant:
            relevant.append("No relevant findings were available for this source.")
        if not context:
            context.append("Source included for clinician review.")

        return relevant, context

    def _html_case_overview(self, case_id: str, generated_at: str, generated_timezone: str, patient: dict[str, Any]) -> str:
        items = [
            ("Case ID", case_id),
            ("Generated", generated_at),
            ("Display timezone", generated_timezone),
            ("Selected panel", self._format_panel_label(patient.get("selected_panel"))),
            ("Patient age", patient.get("age")),
            ("Patient sex", patient.get("sex")),
            ("Symptoms", self._join(patient.get("symptoms", []))),
            ("Clinical notes", patient.get("clinical_notes")),
        ]
        return self._html_card_grid("Case Overview", items)

    def _html_summary(self, summary: dict[str, int]) -> str:
        cards = "".join(
            f'<div class="card"><small>{self._esc(label)}</small><strong>{value}</strong></div>'
            for label, value in summary.items()
        )
        return f"<section><h2>Review Summary</h2><div class=\"grid\">{cards}</div></section>"

    def _html_severity(self, severity: Any) -> str:
        if not isinstance(severity, dict):
            return ""

        label = self._display(severity.get("label"))
        key = label.lower() if label.lower() in {"routine", "urgent", "critical"} else "unknown"

        return (
            f'<section class="severity {self._esc(key)}">'
            "<h2>Severity Support Alert</h2>"
            f"<p><strong>Severity label:</strong> {self._esc(label)}</p>"
            f"<p><strong>Confidence:</strong> {self._esc(self._format_confidence(severity.get('confidence')))}</p>"
            f"<p><strong>Source:</strong> {self._esc(self._source_label(severity.get('source')))}</p>"
            f"<p>{self._esc(SEVERITY_DISCLAIMER)}</p>"
            "</section>"
        )

    def _html_lab_results(self, labs: list[dict[str, Any]]) -> str:
        rows = []
        for lab in labs:
            status = str(lab.get("status") or "Unknown")
            rows.append(
                "<tr>"
                f"<td>{self._esc(lab.get('test_name'))}</td>"
                f"<td>{self._esc(lab.get('value'))}</td>"
                f"<td>{self._esc(lab.get('unit'))}</td>"
                f"<td>{self._esc(self._range_text(lab))}</td>"
                f"<td>{self._status_badge(status)}</td>"
                f"<td>{self._esc(lab.get('evidence'))}</td>"
                "</tr>"
            )
        if not rows:
            rows.append("<tr><td colspan=\"6\">No lab results were returned.</td></tr>")
        return (
            "<section><h2>Lab Results</h2><table><thead><tr>"
            "<th>Test</th><th>Value</th><th>Unit</th><th>Reference Range</th><th>Status</th><th>Evidence</th>"
            "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></section>"
        )

    def _html_abnormal_findings(self, findings: list[dict[str, Any]]) -> str:
        if not findings:
            body = "<p>No abnormal findings were identified using the configured educational reference ranges.</p>"
        else:
            body = "<ul>" + "".join(
                f"<li><strong>{self._esc(finding.get('test_name'))}</strong>: "
                f"{self._esc(finding.get('value'))} {self._esc(finding.get('unit'))}, "
                f"{self._esc(finding.get('status'))}. Reference range {self._esc(self._range_text(finding))}. "
                f"{self._esc(finding.get('evidence'))}</li>"
                for finding in findings
            ) + "</ul>"
        return f"<section><h2>Abnormal Findings Requiring Clinician Review</h2>{body}</section>"

    def _html_warnings(self, warnings: list[dict[str, Any]]) -> str:
        if not warnings:
            body = "<p>No clinical warnings were returned for this review.</p>"
        else:
            body = "<ul>" + "".join(
                f"<li><strong>{self._esc(warning.get('severity', 'Review'))}</strong>: "
                f"{self._esc(warning.get('text'))} "
                f"<span class=\"muted\">({self._esc(warning.get('associated_item'))})</span></li>"
                for warning in warnings
            ) + "</ul>"
        return f"<section><h2>Clinical Warnings</h2>{body}</section>"

    def _html_patterns(self, patterns: list[dict[str, Any]]) -> str:
        if not patterns:
            return "<section><h2>Top Clinical Patterns</h2><p>No top clinical patterns were returned for this review.</p></section>"

        cards = []
        for pattern in patterns:
            cards.append(
                "<div class=\"card\">"
                f"<h3>Rank {self._esc(pattern.get('rank'))}: {self._esc(normalize_terminal_punctuation(pattern.get('pattern_name')))}</h3>"
                "<p>This pattern may be consistent with the submitted findings and requires clinician review.</p>"
                f"<p><strong>Rank:</strong> {self._esc(pattern.get('rank'))}</p>"
                f"<p><strong>Confidence:</strong> {self._esc(pattern.get('confidence_level'))}</p>"
                f"<p><strong>Score:</strong> {self._esc(pattern.get('score'))}</p>"
                f"<p><strong>Retrieved sources:</strong> {len(pattern.get('retrieved_sources', []))}</p>"
                "</div>"
            )
        return f"<section><h2>Top Clinical Patterns</h2>{''.join(cards)}</section>"

    def _html_missing_labs(self, missing_labs: list[str]) -> str:
        if missing_labs:
            body = "<ul>" + "".join(f"<li>{self._esc(lab)}</li>" for lab in missing_labs) + "</ul>"
            body += "<p>Interpretation may be limited until missing information is reviewed.</p>"
        else:
            body = "<p>No missing required labs were reported for the selected panel.</p>"
        return f"<section><h2>Missing Required Labs</h2>{body}</section>"

    def _html_sources(self, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "<section><h2>Retrieved Evidence Sources</h2><p>No retrieved evidence sources were available for this review.</p></section>"

        cards = []
        for source in sources:
            cards.append(
                "<div class=\"card\">"
                f"<h3>{self._esc(source.get('title'))}</h3>"
                f"<p><strong>Relevant Finding:</strong> {self._esc(source.get('snippet'))}</p>"
                f"<p><strong>Clinical Context:</strong> {self._esc(source.get('pattern_code'))}</p>"
                f"<p><strong>Similarity Score:</strong> {self._esc(self._format_score(source.get('similarity_score')))}</p>"
                f"<p><strong>Source ID:</strong> {self._esc(source.get('source_id'))}</p>"
                "</div>"
            )
        return f"<section><h2>Retrieved Evidence Sources</h2>{''.join(cards)}</section>"

    def _html_limitations(self) -> str:
        return (
            "<section><h2>Clinical Interpretation Limitations</h2><ul>"
            "<li>Configured ranges are educational.</li>"
            "<li>Ranges may differ by lab, age, sex, method, and clinical context.</li>"
            "<li>This output supports review and does not replace clinician judgment.</li>"
            "<li>This output is not a final diagnosis.</li>"
            "<li>No medication or treatment recommendation is provided.</li>"
            "</ul></section>"
        )

    def _html_card_grid(self, title: str, items: list[tuple[str, Any]]) -> str:
        cards = "".join(
            f'<div class="card"><small>{self._esc(label)}</small><strong>{self._esc(value)}</strong></div>'
            for label, value in items
        )
        return f"<section><h2>{self._esc(title)}</h2><div class=\"grid\">{cards}</div></section>"

    def _status_badge(self, status: str) -> str:
        key = status.lower() if status.lower() in {"normal", "low", "high", "critical", "unknown"} else "unknown"
        return f'<span class="badge {key}">{self._esc(status)}</span>'

    def _join(self, values: Any) -> str:
        if isinstance(values, list):
            cleaned = [self._display(value) for value in values if self._display(value) != "Not available"]
            return ", ".join(cleaned) or "Not available"

        return self._display(values)

    def _range_text(self, lab: dict[str, Any]) -> str:
        low = lab.get("reference_low")
        high = lab.get("reference_high")

        if low is None and high is None:
            return "Not available"

        return f"{self._display(low)}-{self._display(high)}"

    def _format_score(self, value: Any) -> str:
        if value is None:
            return "Not available"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return self._display(value)

    def _format_confidence(self, value: Any) -> str:
        if value is None:
            return "Not available"

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return "Not available"

        numeric_value = max(0.0, min(1.0, numeric_value))
        return f"{round(numeric_value * 100):.0f}%"

    def _source_label(self, value: Any) -> str:
        labels = {
            "fine_tuned_model": "Fine-tuned DistilBERT model",
            "rule_based_fallback": "Rule-based fallback",
            "critical_override": "Critical lab override",
        }
        return labels.get(str(value or ""), self._display(value))

    def _display(self, value: Any) -> str:
        if value is None or value == "":
            return "Not available"
        return sanitize_text(str(value))

    def _format_panel_label(self, value: Any) -> str:
        if value is None or value == "":
            return "Not available"
        text = self._display(value)
        mapping = {
            "Diabetic_Panel": "Diabetic / Rapid Glucose Panel",
            "Cardiac_Enzymes_Panel": "Cardiac Enzymes Panel",
            "Electrolytes_Calcium_Panel": "Electrolytes & Calcium Panel",
            "Lipids_Inflammation_Panel": "Lipids & Inflammation Panel",
            "Albumin_Protein_Panel": "Albumin & Protein Panel",
            "Renal_Thyroid_Panel": "Renal & Thyroid Panel",
        }
        return mapping.get(text, text)

    def _md_cell(self, value: Any) -> str:
        return self._display(value).replace("|", "\\|").replace("\n", " ")

    def _esc(self, value: Any) -> str:
        return html.escape(self._display(value), quote=True)
