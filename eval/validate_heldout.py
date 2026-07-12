import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HELDOUT_PATH = ROOT / "eval" / "heldout.jsonl"
REQUIRED_CASE_FIELDS = {
    "case_id",
    "age",
    "sex",
    "selected_panel",
    "symptoms",
    "clinical_notes",
    "labs",
    "expected_patterns",
    "expected_abnormal_findings",
    "expected_missing_labs",
    "expected_severity",
    "expected_safety_notice",
    "source_reference",
    "source_type",
    "validation_notes",
}
ALLOWED_SOURCE_TYPES = {
    "published_case_derived",
    "guideline_based",
    "educational_case",
    "deidentified_public_case",
}
ALLOWED_SEVERITY_LABELS = {"Routine", "Urgent", "Critical"}
UNSAFE_PHRASES = (
    "the patient has ",
    "diagnosed with ",
    "diagnosis is ",
    "treatment plan",
    "prescribe",
    "start medication",
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_cases(path: Path = DEFAULT_HELDOUT_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Held-out file not found: {path}")

    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            raise ValueError(f"Line {line_number} is empty")
        try:
            case = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Malformed JSON on line {line_number}: {error}") from error
        if not isinstance(case, dict):
            raise ValueError(f"Line {line_number} must contain an object")
        cases.append(case)
    return cases


def validate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    panels = load_json(ROOT / "data" / "panel_templates.json")
    ranges = load_json(ROOT / "data" / "reference_ranges.json")
    patterns = load_json(ROOT / "data" / "clinical_patterns.json")
    pattern_names = set(patterns.get("patterns", patterns))
    errors: list[str] = []
    ids: list[str] = []
    fingerprints: list[str] = []

    if len(cases) < 50:
        errors.append(f"Expected at least 50 cases, found {len(cases)}")

    for index, case in enumerate(cases, 1):
        label = str(case.get("case_id", f"line {index}"))
        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{label}: missing fields {sorted(missing)}")
            continue

        ids.append(str(case["case_id"]))
        panel_name = case["selected_panel"]
        panel = panels.get(panel_name)
        if not isinstance(panel, dict):
            errors.append(f"{label}: unsupported panel {panel_name!r}")
            supported_tests: dict[str, str | None] = {}
        else:
            supported_tests = {item["name"]: item.get("unit") for item in panel.get("tests", [])}

        if not isinstance(case["age"], int) or not 0 < case["age"] <= 120:
            errors.append(f"{label}: age must be an integer from 1 through 120")
        if not isinstance(case["sex"], str) or not case["sex"].strip():
            errors.append(f"{label}: sex must be a non-empty string")
        if not isinstance(case["symptoms"], list) or not all(isinstance(x, str) for x in case["symptoms"]):
            errors.append(f"{label}: symptoms must be a list of strings")
        if not isinstance(case["labs"], list) or not case["labs"]:
            errors.append(f"{label}: labs must be a non-empty list")
        else:
            for lab in case["labs"]:
                if not isinstance(lab, dict) or set(lab) != {"name", "value", "unit"}:
                    errors.append(f"{label}: each lab must contain only name, value, and unit")
                    continue
                name = lab["name"]
                if name not in supported_tests:
                    errors.append(f"{label}: {name!r} is not supported by {panel_name}")
                if name not in ranges:
                    errors.append(f"{label}: {name!r} has no configured reference range")
                expected_unit = supported_tests.get(name)
                if lab["unit"] != expected_unit:
                    errors.append(f"{label}: {name} unit {lab['unit']!r} != {expected_unit!r}")
                if not isinstance(lab["value"], (int, float)) or isinstance(lab["value"], bool):
                    errors.append(f"{label}: {name} value must be numeric")

        if not isinstance(case["expected_patterns"], list):
            errors.append(f"{label}: expected_patterns must be a list")
        else:
            unknown_patterns = set(case["expected_patterns"]) - pattern_names
            if unknown_patterns:
                errors.append(f"{label}: unknown patterns {sorted(unknown_patterns)}")
        if case["expected_safety_notice"] != "For clinicians only — supports review, not diagnosis or prescribing.":
            errors.append(f"{label}: expected safety notice is not canonical")
        if case.get("expected_severity") not in ALLOWED_SEVERITY_LABELS:
            errors.append(f"{label}: expected_severity must be Routine, Urgent, or Critical")
        if case["source_type"] not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{label}: unsupported source_type {case['source_type']!r}")
        source = case["source_reference"]
        if not isinstance(source, dict) or not all(source.get(k) for k in ("title", "publisher", "url")):
            errors.append(f"{label}: source_reference requires title, publisher, and url")

        text = json.dumps(case, ensure_ascii=False).lower()
        for phrase in UNSAFE_PHRASES:
            if re.search(rf"\b{re.escape(phrase)}", text):
                errors.append(f"{label}: unsafe wording contains {phrase!r}")

        fingerprints.append(json.dumps({k: case[k] for k in ("age", "sex", "selected_panel", "symptoms", "labs")}, sort_keys=True))

    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"Duplicate case IDs: {duplicate_ids}")
    duplicate_cases = sum(count - 1 for count in Counter(fingerprints).values() if count > 1)
    if duplicate_cases:
        errors.append(f"Found {duplicate_cases} exact duplicate case payloads")

    distribution = Counter(case.get("selected_panel") for case in cases)
    missing_panels = set(panels) - set(distribution)
    if missing_panels:
        errors.append(f"Panels without evaluation cases: {sorted(missing_panels)}")

    if errors:
        raise ValueError("Held-out validation failed:\n- " + "\n- ".join(errors))
    return {"total_cases": len(cases), "panel_distribution": dict(sorted(distribution.items()))}


def main() -> None:
    summary = validate_cases(load_cases())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
