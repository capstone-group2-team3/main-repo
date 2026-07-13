from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.db.repositories import (
    add_lab_results,
    add_pattern_results,
    create_report_case,
    save_generated_report,
)
from app.db.severity_repositories import save_case_severity
from app.services.clinical_pattern_scorer import ClinicalPatternScorer
from app.services.evidence_retrieval_agent import EvidenceRetrievalAgent
from app.services.lab_analysis_agent import LabAnalysisAgent
from app.services.lab_normalizer import LabNormalizer
from app.services.panel_template_service import PanelTemplateService
from app.services.severity_classifier_service import severity_service
from app.services.report_generator_agent import REPORT_FORMAT_VERSION, ReportGeneratorAgent
from app.services.safety_agent import SAFETY_NOTICE, sanitize_dashboard

class AgentOrchestrator:
    def __init__(self):
        self.normalizer = LabNormalizer()
        self.panel_template_service = PanelTemplateService()
        self.lab_analysis_agent = LabAnalysisAgent(normalizer=self.normalizer)
        self.clinical_pattern_scorer = ClinicalPatternScorer(normalizer=self.normalizer)
        self.evidence_retrieval_agent = EvidenceRetrievalAgent()
        self.report_generator_agent = ReportGeneratorAgent()

    def _build_abnormal_findings(self, lab_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "test": result["test_name"],
                "value": result["value"],
                "unit": result.get("unit"),
                "status": result["status"],
                "evidence": result["evidence"],
            }
            for result in lab_results
            if result["status"] not in {"Normal", "Unknown"}
        ]

    def _build_clinical_warnings(
        self,
        lab_results: list[dict[str, Any]],
        clinical_patterns: list[dict[str, Any]],
        missing_required_labs: list[str],
    ) -> list[str]:
        warnings: list[str] = []
        has_abnormal_warning = False

        for lab in lab_results:
            specific = self._specific_lab_warning(lab)
            if specific:
                warnings.append(specific)
                has_abnormal_warning = True
            elif lab["status"] == "Critical":
                warnings.append(
                    f"Critical {lab['test_name']} value detected. Requires clinician review."
                )
                has_abnormal_warning = True

        for pattern in clinical_patterns:
            for warning in pattern.get("warnings", []):
                warnings.append(warning)

        for lab_name in missing_required_labs:
            warnings.append(
                f"Missing required lab value for selected panel: {lab_name}."
            )

        if not has_abnormal_warning and any(result["status"] not in {"Normal", "Unknown"} for result in lab_results):
            warnings.append("Abnormal lab values detected. Review in full clinical context.")

        return warnings

    def _specific_lab_warning(self, lab: dict[str, Any]) -> str | None:
        name = str(lab.get("test_name") or "")
        status = str(lab.get("status") or "").lower()
        is_high = status in {"high", "critical high"}
        is_low = status in {"low", "critical low"}
        if status == "critical":
            try:
                value = float(lab.get("value"))
                reference_low = lab.get("reference_low")
                reference_high = lab.get("reference_high")
                is_low = reference_low is not None and value < float(reference_low)
                is_high = reference_high is not None and value > float(reference_high)
            except (TypeError, ValueError):
                pass

        if name == "Creatinine" and is_high:
            return "Elevated creatinine requires clinician review in the context of renal function, hydration status, medications, prior results, and the full clinical picture."
        if name == "Hemoglobin" and is_low:
            return "Low hemoglobin requires clinician review with correlation to symptoms, prior results, and additional hematologic context."
        if name == "Troponin" and is_high:
            return "Elevated troponin requires urgent clinician review in the context of symptoms, ECG findings, timing, repeat measurements, and the full clinical picture."
        if name == "CPK" and is_high:
            return "Elevated CPK requires clinician review in the context of muscle injury, cardiac markers, medications, activity history, and the full clinical picture."
        return None

    def _retrieve_evidence(
        self,
        clinical_patterns: list[dict[str, Any]],
        selected_panel: str | None = None,
        lab_results: list[dict[str, Any]] | None = None,
        symptoms: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        abnormal_labs = [
            lab for lab in lab_results or []
            if lab.get("status") not in {"Normal", "Unknown"}
        ]
        try:
            grouped_sources = self.evidence_retrieval_agent.retrieve_for_patterns(
                clinical_patterns,
                top_k=3,
                selected_panel=selected_panel,
                abnormal_labs=abnormal_labs,
                symptoms=symptoms,
            )
        except RuntimeError:
            raise
        except Exception:
            return []

        flat_sources: list[dict[str, Any]] = []
        for group in grouped_sources:
            if not isinstance(group, dict):
                continue

            pattern_code = group.get("pattern_code")
            sources = group.get("retrieved_sources", [])

            if not isinstance(sources, list):
                continue

            for source in sources:
                if not isinstance(source, dict):
                    continue

                flat_source = dict(source)
                flat_source["pattern_code"] = pattern_code
                flat_sources.append(flat_source)

        return flat_sources

    def analyze_report(self, payload: Any, db: Session) -> dict[str, Any]:
        if isinstance(payload, dict):
            request_data = payload
        elif hasattr(payload, "model_dump"):
            request_data = payload.model_dump()
        else:
            request_data = payload.dict()

        selected_panel = request_data["selected_panel"]
        template = self.panel_template_service.get_template(selected_panel)

        if not template:
            raise ValueError(f"Unknown panel: {selected_panel}")

        case = create_report_case(
            db,
            {
                "age": request_data["age"],
                "sex": request_data["sex"],
                "selected_panel": selected_panel,
                "symptoms": request_data.get("symptoms", []),
                "clinical_notes": request_data.get("clinical_notes"),
            },
        )

        normalized_labs = self.normalizer.normalize_labs(request_data.get("labs", []))
        normalized_symptoms = self.normalizer.normalize_symptoms(request_data.get("symptoms", []))

        missing_required_labs = self.panel_template_service.find_missing_required_labs(
            selected_panel,
            [lab["name"] for lab in normalized_labs],
            self.normalizer,
        )

        lab_results = self.lab_analysis_agent.analyze_labs(selected_panel, normalized_labs)
        add_lab_results(db, case.id, lab_results)

        clinical_patterns = self.clinical_pattern_scorer.score_patterns(
            selected_panel,
            lab_results,
            normalized_symptoms,
        )
        add_pattern_results(db, case.id, clinical_patterns)

        # --- Severity Logic Integration ---
        abnormal_list = [f"{lab['test_name']} {lab['status']}" for lab in lab_results if lab.get("status") not in {"Normal", "Unknown"}]
        abnormal_str = ", ".join(abnormal_list) if abnormal_list else "None"
        
        age_val = request_data.get("age", "Unknown")
        sex_val = request_data.get("sex", "Unknown")
        symptoms_str = ", ".join(normalized_symptoms) if normalized_symptoms else "None"
        
        case_text = f"Age: {age_val}, Sex: {sex_val}, Panel: {selected_panel}. Abnormal: {abnormal_str}. Symptoms: {symptoms_str}."
        has_critical_lab = any(lab.get("status") == "Critical" for lab in lab_results)

        severity_result = severity_service.predict_severity(
            case_text=case_text,
            lab_results=lab_results,
            clinical_patterns=clinical_patterns,
            has_critical_lab_value=has_critical_lab,
        )

        save_case_severity(
            db=db,
            case_id=case.id,
            severity_label=severity_result["label"],
            confidence=severity_result["confidence"],
            source=severity_result["source"]
        )

        abnormal_findings = self._build_abnormal_findings(lab_results)
        retrieved_sources = self._retrieve_evidence(
            clinical_patterns,
            selected_panel=selected_panel,
            lab_results=lab_results,
            symptoms=normalized_symptoms,
        )
        clinical_warnings = self._build_clinical_warnings(
            lab_results,
            clinical_patterns,
            missing_required_labs,
        )

        case_data = {
            "age": request_data["age"],
            "sex": request_data["sex"],
            "selected_panel": selected_panel,
            "symptoms": normalized_symptoms,
            "clinical_notes": request_data.get("clinical_notes"),
        }

        generated_at = datetime.now(timezone.utc).isoformat()
        dashboard = self.report_generator_agent.build_dashboard(
            case_data=case_data,
            lab_results=lab_results,
            clinical_patterns=clinical_patterns,
            retrieved_sources=retrieved_sources,
            clinical_warnings=clinical_warnings,
            missing_required_labs=missing_required_labs,
            generated_at=generated_at,
        )

        dashboard.update(
            {
                "message": "Analysis pipeline completed using local JSON configuration files.",
                "report_case_id": case.id,
                "received": request_data,
                "severity": severity_result,
            }
        )

        dashboard = sanitize_dashboard(dashboard)
        markdown_path, html_path = self.report_generator_agent.build_report_paths(case.id, generated_at)
        pdf_path = self.report_generator_agent.pdf_path_from_markdown_path(markdown_path)
        dashboard["report_file_path"] = markdown_path
        dashboard["report_format_version"] = REPORT_FORMAT_VERSION
        dashboard["report"] = {
            "generated": True,
            "markdown_path": markdown_path,
            "html_path": html_path,
            "pdf_path": pdf_path,
            "markdown_download_url": f"/reports/{case.id}/download/markdown",
            "html_download_url": f"/reports/{case.id}/download/html",
            "pdf_download_url": f"/reports/{case.id}/download/pdf",
        }

        markdown = self.report_generator_agent.render_markdown(dashboard)
        html_report = self.report_generator_agent.render_html(dashboard)
        report_file_path = self.report_generator_agent.save_markdown_report(
            case.id,
            markdown,
            generated_at,
            path=markdown_path,
        )
        html_file_path = self.report_generator_agent.save_html_report(
            case.id,
            html_report,
            generated_at,
            path=html_path,
        )
        pdf_file_path = self.report_generator_agent.render_pdf(dashboard, pdf_path)
        save_generated_report(db, case.id, markdown, report_file_path)
        dashboard["report_file_path"] = report_file_path
        dashboard["report"]["markdown_path"] = report_file_path
        dashboard["report"]["html_path"] = html_file_path
        dashboard["report"]["pdf_path"] = pdf_file_path

        for pattern in dashboard.get("clinical_patterns", []):
            if isinstance(pattern, dict):
                pattern.setdefault("pattern", pattern.get("pattern_name"))

        # --- Combined Structured Response Including Severity Info ---
        return {
            "message": "Analysis pipeline completed using local JSON configuration files.",
            "report_case_id": case.id,
            "received": request_data,
            "patient_summary": {
                "age": request_data["age"],
                "sex": request_data["sex"],
                "selected_panel": selected_panel,
                "symptoms": normalized_symptoms,
                "clinical_notes": request_data.get("clinical_notes"),
            },
            "lab_results": lab_results,
            "abnormal_findings": abnormal_findings,
            "clinical_warnings": clinical_warnings,
            "clinical_patterns": [
                {
                    "rank": pattern["rank"],
                    "pattern_code": pattern["pattern_code"],
                    "pattern": pattern["pattern_name"],
                    "score": pattern["score"],
                    "confidence_level": pattern["confidence_level"],
                    "evidence_for": pattern["evidence_for"],
                    "missing_evidence": pattern["missing_evidence"],
                    "recommended_clinician_review": pattern["recommended_clinician_review"],
                }
                for pattern in clinical_patterns
            ],
            "severity": {
                "label": severity_result["label"],
                "confidence": severity_result["confidence"],
                "source": severity_result["source"],
            },
            "retrieved_sources": retrieved_sources,
            "missing_required_labs": missing_required_labs,
            "safety_notice": SAFETY_NOTICE,
            **dashboard,
        }

__all__ = ["AgentOrchestrator", "SAFETY_NOTICE"]
