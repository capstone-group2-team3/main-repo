from collections import Counter

from eval.validate_heldout import DEFAULT_HELDOUT_PATH, load_cases, validate_cases


def test_heldout_is_valid_and_has_at_least_50_cases():
    cases = load_cases(DEFAULT_HELDOUT_PATH)
    summary = validate_cases(cases)

    assert summary["total_cases"] >= 50


def test_heldout_ids_and_payloads_are_unique():
    cases = load_cases(DEFAULT_HELDOUT_PATH)

    ids = [case["case_id"] for case in cases]
    payloads = [
        repr((case["age"], case["sex"], case["selected_panel"], case["symptoms"], case["labs"]))
        for case in cases
    ]

    assert len(ids) == len(set(ids))
    assert len(payloads) == len(set(payloads))


def test_heldout_uses_request_lab_contract_and_covers_every_panel():
    cases = load_cases(DEFAULT_HELDOUT_PATH)

    distribution = Counter(case["selected_panel"] for case in cases)
    assert all(count >= 1 for count in distribution.values())

    for case in cases:
        for lab in case["labs"]:
            assert set(lab) == {"name", "value", "unit"}
            assert "test_name" not in lab


def test_heldout_has_complete_source_and_expected_output_metadata():
    cases = load_cases(DEFAULT_HELDOUT_PATH)

    for case in cases:
        assert case["source_reference"]["title"]
        assert case["source_reference"]["publisher"]
        assert case["source_reference"]["url"].startswith("https://")
        assert isinstance(case["expected_patterns"], list)
        assert isinstance(case["expected_abnormal_findings"], list)
        assert isinstance(case["expected_missing_labs"], list)
        assert case["expected_severity"] in {"Routine", "Urgent", "Critical"}
        assert case["expected_safety_notice"]
        assert case["validation_notes"]
