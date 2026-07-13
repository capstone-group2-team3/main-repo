from eval.run_eval import calculate_summary
from eval.run_baseline import DEFAULT_HELDOUT_PATH, calculate_majority_baseline


def _result(expected: str, predicted: str) -> dict:
    return {
        "status": "success",
        "selected_panel": "CBC_Panel",
        "top3_pattern_recall": 1.0,
        "evidence_grounded": True,
        "latency_ms": 10.0,
        "safety_notice_present": True,
        "abnormal_findings_match": True,
        "expected_severity": expected,
        "predicted_severity": predicted,
        "severity_correct": expected == predicted,
    }


def test_calculate_summary_includes_severity_accuracy_and_critical_recall():
    summary = calculate_summary([
        _result("Routine", "Routine"),
        _result("Urgent", "Routine"),
        _result("Critical", "Critical"),
        _result("Critical", "Urgent"),
    ])

    assert summary["severity_accuracy"] == 0.5
    assert summary["critical_recall"] == 0.5


def test_calculate_summary_handles_zero_expected_critical_cases():
    summary = calculate_summary([
        _result("Routine", "Routine"),
        _result("Urgent", "Urgent"),
    ])

    assert summary["severity_accuracy"] == 1.0
    assert summary["critical_recall"] == 1.0


def test_majority_baseline_uses_same_heldout_severity_metric():
    output = calculate_majority_baseline(DEFAULT_HELDOUT_PATH, final_results_path=None)

    assert output["summary"]["baseline_name"] == "majority_severity_class"
    assert output["summary"]["majority_label"] == "Urgent"
    assert output["summary"]["heldout_cases"] == 57
    assert output["summary"]["primary_metric"] == "severity_accuracy"
    assert output["summary"]["severity_accuracy"] == 0.9123
    assert output["summary"]["critical_recall"] == 0.0
