import json
from pathlib import Path

class ClinicalPatternScorer:
    def __init__(self, patterns_path: str = "data/clinical_patterns.json", normalizer=None):
        raw_path = Path(patterns_path)
        if raw_path.is_absolute():
            self.patterns_path = raw_path
        else:
            project_root = Path(__file__).resolve().parents[2]
            self.patterns_path = project_root / raw_path
        self.normalizer = normalizer
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> dict:
        with self.patterns_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _condition_matched(self, condition: dict, abnormal_labs: list[dict]) -> bool:
        for lab in abnormal_labs:
            if lab.get("test_name") != condition.get("lab"):
                continue
            wanted_status = condition.get("status")
            actual_status = lab.get("status")
            if wanted_status == "Abnormal":
                return actual_status in ("Low", "High", "Critical")
            return actual_status == wanted_status
        return False

    def score_patterns(self, selected_panel: str, lab_results: list[dict], symptoms: list[str] = None) -> list[dict]:
        abnormal_labs = [lab for lab in lab_results if lab.get("status") not in ("Normal", "Unknown")]
        results = []

        for pattern_code, pattern in self.patterns.items():
            conditions = pattern.get("conditions", [])
            logic = pattern.get("logic", "AND")
            matched = [c for c in conditions if self._condition_matched(c, abnormal_labs)]
            matched_count = len(matched)

            if logic == "OR":
                triggered = matched_count >= 1
            else:
                triggered = matched_count == len(conditions) and len(conditions) > 0

            if not triggered:
                continue

            score = matched_count

            if logic == "OR":
                confidence = "high" if matched_count == len(conditions) else "moderate"
            else:
                confidence = "high"

            evidence_for = [f"{c['lab']} {c['status']}" for c in matched]
            missing_evidence = [f"{c['lab']} {c['status']}" for c in conditions if c not in matched]

            results.append({
                "pattern_code": pattern_code,
                "pattern_name": pattern.get("description", pattern_code.replace("_", " ").title()),
                "score": score,
                "confidence_level": confidence,
                "evidence_for": evidence_for,
                "missing_evidence": missing_evidence,
                "recommended_clinician_review": [],
                "warnings": [],
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        top3 = results[:3]
        for i, r in enumerate(top3):
            r["rank"] = i + 1
        return top3