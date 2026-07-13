import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_PATH = ROOT / "eval" / "results.json"
DEFAULT_OUTPUT_PATH = ROOT / "eval" / "error_analysis.json"


def build_error_analysis(results_path: Path) -> dict[str, Any]:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    cases = results.get("cases", [])
    failures = [case for case in cases if case.get("failure_reasons")]

    by_panel = Counter(case.get("selected_panel", "unknown") for case in failures)
    by_reason: Counter[str] = Counter()
    by_severity_source = Counter(str(case.get("severity_source") or "none") for case in failures)
    heatmap: dict[str, Counter[str]] = defaultdict(Counter)

    for case in failures:
        panel = str(case.get("selected_panel") or "unknown")
        for reason in case.get("failure_reasons", []):
            reason = str(reason)
            by_reason[reason] += 1
            heatmap[panel][reason] += 1

    documented_failures = [
        {
            "case_id": case.get("case_id"),
            "input_summary": case.get("input_summary"),
            "expected_patterns": case.get("expected_patterns"),
            "predicted_top3": case.get("predicted_top3"),
            "expected_severity": case.get("expected_severity"),
            "predicted_severity": case.get("predicted_severity"),
            "severity_source": case.get("severity_source"),
            "failure_reasons": case.get("failure_reasons"),
        }
        for case in failures[:10]
    ]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_results": str(results_path.relative_to(ROOT)),
        "total_cases": len(cases),
        "failure_count": len(failures),
        "grouped_by_panel": dict(sorted(by_panel.items())),
        "grouped_by_failure_reason": dict(sorted(by_reason.items())),
        "grouped_by_severity_source": dict(sorted(by_severity_source.items())),
        "panel_reason_heatmap": {
            panel: dict(sorted(reasons.items()))
            for panel, reasons in sorted(heatmap.items())
        },
        "documented_failure_cases": documented_failures,
        "next_iteration_hypothesis": (
            "Most observed failures are severity-accuracy mismatches on non-critical cases; "
            "rebalance and calibrate the severity classifier while preserving the deterministic "
            "critical override that protects Critical recall."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate grouped MedDx evaluation error analysis.")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    output = build_error_analysis(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "failure_count": output["failure_count"],
        "grouped_by_failure_reason": output["grouped_by_failure_reason"],
        "grouped_by_panel": output["grouped_by_panel"],
    }, indent=2, ensure_ascii=False))
    print(f"Saved error analysis to {args.output}")


if __name__ == "__main__":
    main()
