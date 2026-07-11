import json
from collections import Counter
from pathlib import Path

HELDOUT_PATH = Path("eval/heldout.jsonl")

EXPECTED_DISTRIBUTION = {
    "CBC_Panel": 7,
    "Diabetic_Panel": 7,
    "Renal_Thyroid_Panel": 6,
    "Lipids_Inflammation_Panel": 6,
    "Cardiac_Enzymes_Panel": 6,
    "Electrolytes_Calcium_Panel": 6,
    "Coagulation_Panel": 4,
    "Albumin_Protein_Panel": 4,
    "Pancreatic_Salivary_Enzyme_Panel": 4,
}


def load_cases():
    assert HELDOUT_PATH.exists(), "eval/heldout.jsonl does not exist."

    cases = []
    for line_number, line in enumerate(HELDOUT_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()

        assert line, f"Line {line_number} is empty."
        assert not line.startswith("#"), f"Line {line_number} is a comment. JSONL must contain JSON only."

        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise AssertionError(f"Line {line_number} is not valid JSON: {error}") from error

    return cases


def test_heldout_has_50_cases():
    cases = load_cases()

    assert len(cases) == 50


def test_heldout_ids_are_unique():
    cases = load_cases()

    ids = [case["id"] for case in cases]

    assert len(ids) == len(set(ids))


def test_heldout_schema_shape():
    cases = load_cases()

    for case in cases:
        assert "id" in case
        assert "input" in case
        assert "expected" in case
        assert "metadata" in case

        payload = case["input"]
        assert isinstance(payload["age"], int)
        assert isinstance(payload["sex"], str)
        assert isinstance(payload["selected_panel"], str)
        assert isinstance(payload["symptoms"], list)
        assert isinstance(payload["labs"], list)
        assert len(payload["labs"]) >= 1

        for lab in payload["labs"]:
            assert "name" in lab
            assert "value" in lab
            assert "unit" in lab
            assert isinstance(lab["name"], str)
            assert isinstance(lab["value"], (int, float))

        assert isinstance(case["expected"], list)
        assert len(case["expected"]) >= 1
        assert all(isinstance(pattern, str) for pattern in case["expected"])


def test_heldout_distribution_by_panel():
    cases = load_cases()

    distribution = Counter(case["input"]["selected_panel"] for case in cases)

    assert distribution == EXPECTED_DISTRIBUTION