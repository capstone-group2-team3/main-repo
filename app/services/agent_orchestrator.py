from typing import Any
from sqlalchemy.orm import Session

from app.db.repositories import add_lab_results, add_pattern_results, create_report_case
from app.db.severity_repositories import save_case_severity
from app.services.clinical_pattern_scorer import ClinicalPatternScorer
from app.services.lab_analysis_agent import LabAnalysisAgent
from app.services.lab_normalizer import LabNormalizer
from app.services.panel_template_service import PanelTemplateService
from app.services.severity_classifier_service import severity_service

SAFETY_NOTICE = (
    "This tool supports clinician review only. It does not provide a final diagnosis, "
    "does not prescribe medication, and does not replace physician judgment."
)

class AgentOrchestrator:
    def __init__(self):
        self.normalizer = LabNormalizer()
        self.panel_template_service = PanelTemplateService()
        self.lab_analysis_agent = LabAnalysisAgent(normalizer=self.normalizer)
        self.clinical_pattern_scorer = ClinicalPatternScorer(normalizer=self.normalizer)

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

        for lab in lab_results:
            if lab["status"] == "Critical":
                warnings.append(
                    f"Critical {lab['test_name']} value detected. Requires clinician review."
                )

        for pattern in clinical_patterns:
            for warning in pattern.get("warnings", []):
                warnings.append(warning)

        for lab_name in missing_required_labs:
            warnings.append(
                f"Missing required lab value for selected panel: {lab_name}."
            )

        if not warnings and any(result["status"] not in {"Normal", "Unknown"} for result in lab_results):
            warnings.append("Abnormal lab values detected. Review in full clinical context.")

        return warnings

    def analyze_report(self, payload: Any, db: Session) -> dict[str, Any]:
        request_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

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

        abnormal_list = [f"{lab['test_name']} {lab['status']}" for lab in lab_results if lab.get("status") not in {"Normal", "Unknown"}]
        abnormal_str = ", ".join(abnormal_list) if abnormal_list else "None"
        
        age_val = request_data.get("age", "Unknown")
        sex_val = request_data.get("sex", "Unknown")
        symptoms_str = ", ".join(normalized_symptoms) if normalized_symptoms else "None"
        
        case_text = f"Age: {age_val}, Sex: {sex_val}, Panel: {selected_panel}. Abnormal: {abnormal_str}. Symptoms: {symptoms_str}."
        has_critical_lab = any(lab.get("status") == "Critical" or (str(lab.get("test_name", "")).lower() == "hemoglobin" and float(lab.get("value", 0)) < 7.0) for lab in lab_results)

        critical_keywords = ["chest pain", "jaw pain", "shortness of breath", "stroke", "heart attack"]
        has_critical_symptom = any(keyword in case_text.lower() for keyword in critical_keywords)
        is_hard_override = has_critical_lab or has_critical_symptom

        severity_result = severity_service.predict_severity(
            case_text=case_text,
            has_critical_lab_value=is_hard_override
        )

        save_case_severity(
            db=db,
            case_id=case.id,
            severity_label=severity_result["severity_label"],
            confidence=severity_result["confidence"],
            source=severity_result["source"]
        )

        abnormal_findings = self._build_abnormal_findings(lab_results)
        clinical_warnings = self._build_clinical_warnings(
            lab_results,
            clinical_patterns,
            missing_required_labs,
        )

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
                "label": severity_result["severity_label"],
                "confidence": severity_result["confidence"],
                "source": severity_result["source"],
            },
            "retrieved_sources": [],
            "missing_required_labs": missing_required_labs,
            "safety_notice": SAFETY_NOTICE,
        }