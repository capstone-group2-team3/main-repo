import html
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.safety_agent import SAFETY_NOTICE, ensure_safety_notice, sanitize_text


REPORT_FORMAT_VERSION = "1.0"
REPORT_OUTPUT_DIR = Path("reports/generated_reports")


class ReportGeneratorAgent:
    def build_dashboard(
        self,
        case_data: dict[str, Any],
        lab_results: list[dict[str, Any]],
        clinical_patterns: list[dict[str, Any]],
        retrieved_sources: list[dict[str, Any]] | None = None,
        clinical_warnings: list[Any] | None = None,
        missing_required_labs: list[str] | None = None,
    ) -> dict[str, Any]:
        sources = retrieved_sources or []
        source_map = self._sources_by_pattern(sources)
        generated_at = datetime.utcnow().replace(microsecond=0).isoformat()

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
        summary = self._review_summary(dashboard_json)
        case_id = self._display(dashboard_json.get("report_case_id") or dashboard_json.get("case_id"))
        generated_at = self._display(dashboard_json.get("generated_at"))

        lines = [
            "# MedDx Clinical Review Report",
            "",
            "## Clinical Safety Notice",
            f"> {SAFETY_NOTICE}",
            "",
            "## Case Overview",
            f"- Case ID: {case_id}",
            f"- Generated date/time: {generated_at}",
            f"- Selected panel: {self._display(patient.get('selected_panel'))}",
            f"- Patient age: {self._display(patient.get('age'))}",
            f"- Patient sex: {self._display(patient.get('sex'))}",
            f"- Symptoms: {self._join(patient.get('symptoms', []))}",
            f"- Clinical notes: {self._display(patient.get('clinical_notes'))}",
            "",
            "## Review Summary",
        ]

        for label, value in summary.items():
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
                        f"### Rank {self._display(pattern.get('rank'))}: {self._display(pattern.get('pattern_name'))}",
                        "This pattern may be consistent with the submitted findings and requires clinician review.",
                        f"- Confidence level: {self._display(pattern.get('confidence_level'))}",
                        f"- Score: {self._display(pattern.get('score'))}",
                        f"- Evidence for: {self._join(pattern.get('evidence_for', []))}",
                        f"- Missing evidence: {self._join(pattern.get('missing_evidence', []))}",
                        f"- Warnings: {self._join(pattern.get('warnings', []))}",
                        f"- Retrieved evidence sources: {len(pattern.get('retrieved_sources', []))}",
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
                        f"- Source ID: {self._display(source.get('source_id'))}",
                        f"- Similarity score: {self._format_score(source.get('similarity_score'))}",
                        f"- Snippet: {self._display(source.get('snippet'))}",
                        f"- Related pattern: {self._display(source.get('pattern_code'))}",
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
                f"- Report generation timestamp: {generated_at}",
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
        summary = self._review_summary(dashboard_json)
        case_id = self._display(dashboard_json.get("report_case_id") or dashboard_json.get("case_id"))
        generated_at = self._display(dashboard_json.get("generated_at"))

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
    <p>Clinical Review Report • Case {self._esc(case_id)} • Generated {self._esc(generated_at)}</p>
  </header>
  <section class="notice">{self._esc(SAFETY_NOTICE)}</section>
  {self._html_case_overview(case_id, generated_at, patient)}
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

        while markdown_path.exists() or html_path.exists():
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

    def _sources_by_pattern(self, sources: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        source_map: dict[str, list[dict[str, Any]]] = {}

        for source in sources:
            pattern_code = source.get("pattern_code")
            if pattern_code:
                source_map.setdefault(pattern_code, []).append(self._retrieved_source(source))

        return source_map

    def _html_case_overview(self, case_id: str, generated_at: str, patient: dict[str, Any]) -> str:
        items = [
            ("Case ID", case_id),
            ("Generated", generated_at),
            ("Selected panel", patient.get("selected_panel")),
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
                f"<h3>Rank {self._esc(pattern.get('rank'))}: {self._esc(pattern.get('pattern_name'))}</h3>"
                "<p>This pattern may be consistent with the submitted findings and requires clinician review.</p>"
                f"<p><strong>Confidence:</strong> {self._esc(pattern.get('confidence_level'))} "
                f"<strong>Score:</strong> {self._esc(pattern.get('score'))}</p>"
                f"<p><strong>Evidence for:</strong> {self._esc(self._join(pattern.get('evidence_for', [])))}</p>"
                f"<p><strong>Missing evidence:</strong> {self._esc(self._join(pattern.get('missing_evidence', [])))}</p>"
                f"<p><strong>Warnings:</strong> {self._esc(self._join(pattern.get('warnings', [])))}</p>"
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
                f"<p><strong>Source ID:</strong> {self._esc(source.get('source_id'))}</p>"
                f"<p><strong>Similarity score:</strong> {self._esc(self._format_score(source.get('similarity_score')))}</p>"
                f"<p><strong>Related pattern:</strong> {self._esc(source.get('pattern_code'))}</p>"
                f"<p>{self._esc(source.get('snippet'))}</p>"
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

    def _display(self, value: Any) -> str:
        if value is None or value == "":
            return "Not available"
        return sanitize_text(str(value))

    def _md_cell(self, value: Any) -> str:
        return self._display(value).replace("|", "\\|").replace("\n", " ")

    def _esc(self, value: Any) -> str:
        return html.escape(self._display(value), quote=True)
