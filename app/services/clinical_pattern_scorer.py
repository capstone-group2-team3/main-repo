import json
from pathlib import Path
from typing import Any

from app.services.lab_normalizer import LabNormalizer


class ClinicalPatternScorer:
    def __init__(
        self,
        patterns_path: str = "data/clinical_patterns.json",
        normalizer: LabNormalizer | None = None,
    ):
        self.patterns_path = Path(patterns_path)
        self.normalizer = normalizer or LabNormalizer()
        self.patterns = self._load_patterns()

    def _load_json(self) -> dict[str, Any]:
        if not self.patterns_path.exists():
            raise FileNotFoundError(f"Clinical patterns file not found: {self.patterns_path}")

        with self.patterns_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_patterns(self) -> list[dict[str, Any]]:
        raw = self._load_json()
        patterns = raw.get("patterns", raw)

        if isinstance(patterns, dict):
            return list(patterns.values())

        if isinstance(patterns, list):
            return patterns

        return []

    def _status_matches(self, actual_status: str, expected_status: str) -> bool:
        actual = actual_status.lower()
        expected = expected_status.lower()

        if expected == "abnormal":
            return actual not in {"normal", "unknown"}

        if expected == "high":
            return actual in {"high", "critical"}

        if expected == "low":
            return actual in {"low", "critical"}

        if expected == "critical":
            return actual == "critical"

        return actual == expected

    def _confidence_level(self, required_matched: int, required_total: int, matched_symptoms: list[str]) -> str:
        if required_total > 0 and required_matched == required_total:
            if matched_symptoms:
                return "high"
            return "moderate"
        return "low"

    def score_patterns(
        self,
        selected_panel: str,
        lab_results: list[dict[str, Any]],
        symptoms: list[str],
    ) -> list[dict[str, Any]]:
        normalized_symptoms = {
            self.normalizer.normalize_symptom(symptom) for symptom in symptoms
        }

        lab_status_by_name = {
            self.normalizer.normalize_lab_name(result["test_name"]): result["status"]
            for result in lab_results
        }

        scored_patterns: list[dict[str, Any]] = []

        for pattern in self.patterns:
            pattern_panel = pattern.get("panel")
            if pattern_panel and pattern_panel != selected_panel:
                continue

            required_abnormal_labs = pattern.get("required_abnormal_labs", [])
            supporting_symptoms = pattern.get("supporting_symptoms", [])

            score = 0.0
            evidence_for: list[str] = []
            required_matched_count = 0
            required_total = len(required_abnormal_labs)

            for required in required_abnormal_labs:
                if not isinstance(required, dict):
                    continue

                lab_name = self.normalizer.normalize_lab_name(required.get("lab", ""))
                expected_status = required.get("status", "abnormal")
                actual_status = lab_status_by_name.get(lab_name)

                if actual_status and self._status_matches(actual_status, expected_status):
                    score += 2.0
                    required_matched_count += 1
                    evidence_for.append(f"{lab_name} is {actual_status}")

            matched_symptoms: list[str] = []
            for symptom in supporting_symptoms:
                normalized_symptom = self.normalizer.normalize_symptom(symptom)
                if normalized_symptom in normalized_symptoms:
                    matched_symptoms.append(symptom)

            if matched_symptoms:
                score += min(len(matched_symptoms) * 0.5, 2.0)
                evidence_for.extend([f"Symptom present: {symptom}" for symptom in matched_symptoms])

            if score <= 0:
                continue

            confidence = self._confidence_level(required_matched_count, required_total, matched_symptoms)

            warnings = []
            pattern_code = pattern.get("pattern_code", "")
            pattern_name = pattern.get("pattern_name", "")

            if any(word in pattern_code.lower() for word in ["emergency", "warning", "acute"]):
                warnings.append("This pattern requires clinician review in the appropriate clinical context.")

            scored_patterns.append(
                {
                    "pattern_code": pattern_code,
                    "pattern_name": pattern_name,
                    "score": round(score, 2),
                    "confidence_level": confidence,
                    "evidence_for": evidence_for,
                    "missing_evidence": pattern.get("missing_evidence_template", []),
                    "recommended_clinician_review": pattern.get("recommended_clinician_review", []),
                    "warnings": warnings,
                }
            )

        scored_patterns.sort(key=lambda item: item["score"], reverse=True)

        top_patterns = scored_patterns[:3]

        for index, pattern in enumerate(top_patterns, start=1):
            pattern["rank"] = index

        return top_patterns