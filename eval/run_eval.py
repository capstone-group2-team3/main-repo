import argparse
import json
import os
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from eval.validate_heldout import DEFAULT_HELDOUT_PATH, load_cases, validate_cases
except ModuleNotFoundError:
    from validate_heldout import DEFAULT_HELDOUT_PATH, load_cases, validate_cases


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_RESULTS_PATH = ROOT / "eval" / "results.json"
DEFAULT_FAILURE_PATH = ROOT / "eval" / "failure_cases.md"
SAFETY_NOTICE = "For clinicians only — supports review, not diagnosis or prescribing."


def request_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {key: case[key] for key in ("age", "sex", "selected_panel", "symptoms", "clinical_notes", "labs")}


def pattern_code(item: dict[str, Any]) -> str | None:
    value = item.get("pattern_code") or item.get("code") or item.get("pattern")
    return str(value) if value else None


def normalized_abnormal_findings(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    output = []
    for item in items:
        if not isinstance(item, dict):
            continue
        output.append(
            {
                "name": item.get("name") or item.get("test_name") or item.get("test"),
                "value": item.get("value"),
                "unit": item.get("unit"),
                "status": item.get("status"),
            }
        )
    return output


def source_is_useful(source: dict[str, Any]) -> bool:
    return bool(source.get("source_id") or source.get("title") or source.get("snippet"))


def evaluate_case(case: dict[str, Any], orchestrator: Any, db: Any) -> dict[str, Any]:
    started = time.perf_counter()
    expected_patterns = list(case["expected_patterns"])
    input_summary = {
        "age": case["age"],
        "sex": case["sex"],
        "selected_panel": case["selected_panel"],
        "symptoms": case["symptoms"],
        "labs": case["labs"],
    }
    try:
        response = orchestrator.analyze_report(request_payload(case), db)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        patterns = response.get("clinical_patterns", [])
        predicted = [code for code in (pattern_code(x) for x in patterns[:3]) if code]
        matched = [code for code in expected_patterns if code in predicted]
        recall = len(matched) / len(expected_patterns) if expected_patterns else 1.0
        sources = [x for x in response.get("retrieved_sources", []) if isinstance(x, dict) and source_is_useful(x)]
        grounded_codes = {str(x.get("pattern_code")) for x in sources if x.get("pattern_code")}
        grounding_ok = bool(matched) and all(code in grounded_codes for code in matched)
        safety_ok = response.get("safety_notice") == case["expected_safety_notice"] == SAFETY_NOTICE
        actual_abnormal = normalized_abnormal_findings(response.get("abnormal_findings", []))
        expected_abnormal = normalized_abnormal_findings(case["expected_abnormal_findings"])
        abnormal_ok = actual_abnormal == expected_abnormal
        missing_ok = response.get("missing_required_labs", []) == case["expected_missing_labs"]
        issues = []
        if recall < 1:
            issues.append("pattern_recall")
        if matched and not grounding_ok:
            issues.append("evidence_grounding")
        if not abnormal_ok:
            issues.append("abnormal_findings")
        if not missing_ok:
            issues.append("missing_labs")
        if not safety_ok:
            issues.append("safety_notice")
        return {
            "case_id": case["case_id"],
            "input_summary": input_summary,
            "status": "success",
            "selected_panel": case["selected_panel"],
            "expected_patterns": expected_patterns,
            "predicted_top3": predicted,
            "matched_patterns": matched,
            "top3_pattern_recall": round(recall, 4),
            "evidence_grounded": grounding_ok,
            "safety_notice_present": safety_ok,
            "expected_abnormal_findings": expected_abnormal,
            "actual_abnormal_findings": actual_abnormal,
            "abnormal_findings_match": abnormal_ok,
            "expected_missing_labs": case["expected_missing_labs"],
            "actual_missing_labs": response.get("missing_required_labs", []),
            "retrieved_source_count": len(sources),
            "latency_ms": latency_ms,
            "failure_reasons": issues,
        }
    except Exception as error:
        db.rollback()
        return {
            "case_id": case["case_id"],
            "input_summary": input_summary,
            "status": "error",
            "selected_panel": case["selected_panel"],
            "expected_patterns": expected_patterns,
            "predicted_top3": [],
            "matched_patterns": [],
            "top3_pattern_recall": 0.0,
            "evidence_grounded": False,
            "safety_notice_present": False,
            "expected_abnormal_findings": normalized_abnormal_findings(case["expected_abnormal_findings"]),
            "actual_abnormal_findings": [],
            "abnormal_findings_match": False,
            "expected_missing_labs": case["expected_missing_labs"],
            "actual_missing_labs": [],
            "retrieved_source_count": 0,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "failure_reasons": ["runtime_error"],
            "error": f"{type(error).__name__}: {error}",
        }


def calculate_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    successful = sum(item["status"] == "success" for item in results)
    denominator = total or 1
    return {
        "total_cases": total,
        "successful_cases": successful,
        "failed_cases": total - successful,
        "top3_pattern_recall": round(sum(x["top3_pattern_recall"] for x in results) / denominator, 4),
        "evidence_grounding_rate": round(sum(bool(x["evidence_grounded"]) for x in results) / denominator, 4),
        "average_latency_ms": round(sum(x["latency_ms"] for x in results) / denominator, 2),
        "safety_notice_presence_rate": round(sum(bool(x["safety_notice_present"]) for x in results) / denominator, 4),
        "abnormal_findings_match_rate": round(sum(bool(x["abnormal_findings_match"]) for x in results) / denominator, 4),
        "panel_distribution": dict(sorted(Counter(x["selected_panel"] for x in results).items())),
    }


def root_cause(result: dict[str, Any]) -> tuple[str, str, str]:
    reasons = result["failure_reasons"]
    if "runtime_error" in reasons:
        return "implementation bug", "The canonical pipeline raised a runtime error.", "Resolve the recorded exception and rerun the full set."
    if "pattern_recall" in reasons:
        return "pattern logic", "Configured scorer conditions did not return every hand-validated expected pattern in the top three.", "Review pattern conditions, ranking, and panel-specific coverage without weakening safety thresholds."
    if "abnormal_findings" in reasons:
        return "reference ranges", "Returned abnormal findings differ from the configured expected status/value set.", "Reconcile reference-range classification and normalization with the validated fixture."
    if "missing_labs" in reasons:
        return "normalization", "Required-lab detection differs from the validated panel expectation.", "Review canonical lab aliases and required-test matching."
    if "evidence_grounding" in reasons:
        return "retrieval", "A matched pattern had no usable pattern-linked source from the configured evidence index.", "Index authoritative evidence documents and verify Qdrant connectivity and pattern metadata."
    return "implementation bug", "The required safety notice was missing or changed.", "Restore the exact clinician-only safety notice at the pipeline boundary."


def write_failure_analysis(path: Path, results: list[dict[str, Any]], run_at: str) -> int:
    failures = [item for item in results if item["failure_reasons"]]
    lines = [
        "# Held-out Evaluation Failure Cases",
        "",
        f"Generated from `eval/results.json` for the evaluation run at `{run_at}`. These are observed pipeline failures, not invented clinical cases.",
        "",
    ]
    for result in failures:
        category, cause, fix = root_cause(result)
        lines.extend(
            [
                f"## {result['case_id']}",
                "",
                f"- Input summary: `{json.dumps(result['input_summary'], ensure_ascii=False)}`",
                f"- Expected pattern(s): {', '.join(result['expected_patterns']) or 'None'}",
                f"- Predicted pattern(s): {', '.join(result['predicted_top3']) or 'None'}",
                f"- Expected abnormal findings: `{json.dumps(result['expected_abnormal_findings'], ensure_ascii=False)}`",
                f"- Actual abnormal findings: `{json.dumps(result['actual_abnormal_findings'], ensure_ascii=False)}`",
                f"- Retrieved sources count: {result['retrieved_source_count']}",
                f"- Likely root cause: {cause}",
                f"- Proposed fix: {fix}",
                f"- Issue category: {category}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(failures)


def run_eval(heldout_path: Path, output_path: Path, failure_path: Path, limit: int | None = None) -> dict[str, Any]:
    cases = load_cases(heldout_path)
    validate_cases(cases)
    if limit is not None:
        cases = cases[:limit]

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    from app.db import models  # noqa: F401
    from app.db.database import Base
    from app.services.agent_orchestrator import AgentOrchestrator
    import app.services.report_generator_agent as report_module

    with tempfile.TemporaryDirectory(prefix="meddx-eval-") as temp_dir:
        report_module.REPORT_OUTPUT_DIR = Path(temp_dir) / "reports"
        engine = create_engine(f"sqlite:///{Path(temp_dir) / 'eval.db'}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        orchestrator = AgentOrchestrator()
        with session_factory() as db:
            results = []
            for index, case in enumerate(cases, 1):
                print(f"[{index}/{len(cases)}] {case['case_id']}")
                result = evaluate_case(case, orchestrator, db)
                results.append(result)
                print(f"  status={result['status']} recall={result['top3_pattern_recall']:.4f} sources={result['retrieved_source_count']} latency_ms={result['latency_ms']}")
        engine.dispose()

    run_at = datetime.now(timezone.utc).isoformat()
    output = {
        "run_metadata": {
            "run_at_utc": run_at,
            "heldout_path": str(heldout_path),
            "pipeline": "app.services.agent_orchestrator.AgentOrchestrator.analyze_report",
            "case_limit": limit,
        },
        "summary": calculate_summary(results),
        "cases": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    failure_count = write_failure_analysis(failure_path, results, run_at)
    output["run_metadata"]["documented_failure_cases"] = failure_count
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the canonical MedDx pipeline against held-out cases.")
    parser.add_argument("--heldout", type=Path, default=DEFAULT_HELDOUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--failure-output", type=Path, default=DEFAULT_FAILURE_PATH)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    output = run_eval(args.heldout, args.output, args.failure_output, args.limit)
    print(json.dumps(output["summary"], indent=2, ensure_ascii=False))
    print(f"Saved results to {args.output}")
    print(f"Saved failure analysis to {args.failure_output}")


if __name__ == "__main__":
    main()
