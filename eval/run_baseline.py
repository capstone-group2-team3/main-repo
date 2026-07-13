import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from eval.validate_heldout import DEFAULT_HELDOUT_PATH, load_cases, validate_cases
except ModuleNotFoundError:
    from validate_heldout import DEFAULT_HELDOUT_PATH, load_cases, validate_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = ROOT / "eval" / "baseline_results.json"
DEFAULT_FINAL_RESULTS_PATH = ROOT / "eval" / "results.json"


def calculate_majority_baseline(
    heldout_path: Path,
    final_results_path: Path | None = DEFAULT_FINAL_RESULTS_PATH,
) -> dict[str, Any]:
    cases = load_cases(heldout_path)
    validate_cases(cases)

    severity_counts = Counter(case["expected_severity"] for case in cases)
    majority_label = severity_counts.most_common(1)[0][0]
    predictions = []

    for case in cases:
        expected = case["expected_severity"]
        predicted = majority_label
        predictions.append(
            {
                "case_id": case["case_id"],
                "selected_panel": case["selected_panel"],
                "expected_severity": expected,
                "predicted_severity": predicted,
                "severity_correct": predicted == expected,
                "critical_misclassification": expected == "Critical" and predicted != "Critical",
            }
        )

    total = len(predictions)
    expected_critical = [item for item in predictions if item["expected_severity"] == "Critical"]
    critical_recall = (
        sum(item["predicted_severity"] == "Critical" for item in expected_critical) / len(expected_critical)
        if expected_critical
        else 1.0
    )
    summary = {
        "baseline_name": "majority_severity_class",
        "heldout_cases": total,
        "majority_label": majority_label,
        "severity_distribution": dict(sorted(severity_counts.items())),
        "primary_metric": "severity_accuracy",
        "severity_accuracy": round(sum(item["severity_correct"] for item in predictions) / (total or 1), 4),
        "critical_recall": round(critical_recall, 4),
    }

    comparison: dict[str, Any] = {}
    if final_results_path and final_results_path.exists():
        final_results = json.loads(final_results_path.read_text(encoding="utf-8"))
        final_summary = final_results.get("summary", {})
        comparison = {
            "final_system_primary_metric": final_summary.get("severity_accuracy"),
            "baseline_primary_metric": summary["severity_accuracy"],
            "absolute_improvement": (
                round(final_summary["severity_accuracy"] - summary["severity_accuracy"], 4)
                if isinstance(final_summary.get("severity_accuracy"), (int, float))
                else None
            ),
            "final_system_critical_recall": final_summary.get("critical_recall"),
            "baseline_critical_recall": summary["critical_recall"],
        }

    return {
        "run_metadata": {
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "heldout_path": str(heldout_path.relative_to(ROOT)),
            "baseline": "Predict the majority expected severity label for every held-out case.",
            "determinism": "Deterministic; no random seed is used.",
        },
        "summary": summary,
        "comparison_to_final_system": comparison,
        "cases": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MedDx majority-class severity baseline.")
    parser.add_argument("--heldout", type=Path, default=DEFAULT_HELDOUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--final-results", type=Path, default=DEFAULT_FINAL_RESULTS_PATH)
    args = parser.parse_args()

    output = calculate_majority_baseline(args.heldout, args.final_results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output["summary"], indent=2, ensure_ascii=False))
    if output["comparison_to_final_system"]:
        print(json.dumps(output["comparison_to_final_system"], indent=2, ensure_ascii=False))
    print(f"Saved baseline results to {args.output}")


if __name__ == "__main__":
    main()
