import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx


DEFAULT_HELDOUT_PATH = Path("eval/heldout.jsonl")
DEFAULT_RESULTS_PATH = Path("eval/results.json")
DEFAULT_BASE_URL = "http://localhost:8000"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases = []

    if not path.exists():
        raise FileNotFoundError(f"Held-out file not found: {path}")

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()

        if not line:
            continue

        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on line {line_number}: {error}") from error

        cases.append(case)

    return cases


def extract_expected_patterns(case: dict[str, Any]) -> list[str]:
    expected = case.get("expected", [])

    if isinstance(expected, list):
        return [str(item) for item in expected]

    if isinstance(expected, dict):
        patterns = expected.get("patterns", [])
        return [str(item) for item in patterns]

    return []


def extract_clinical_patterns(response_json: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        response_json.get("clinical_patterns"),
        response_json.get("patterns"),
        response_json.get("predicted_patterns"),
    ]

    dashboard = response_json.get("dashboard")
    if isinstance(dashboard, dict):
        candidates.extend(
            [
                dashboard.get("clinical_patterns"),
                dashboard.get("patterns"),
                dashboard.get("predicted_patterns"),
            ]
        )

    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]

    return []


def pattern_code_from_item(pattern: dict[str, Any]) -> str | None:
    for key in ["pattern_code", "code", "id", "pattern"]:
        value = pattern.get(key)
        if value:
            return str(value)

    return None


def extract_predicted_top3(response_json: dict[str, Any]) -> list[str]:
    clinical_patterns = extract_clinical_patterns(response_json)

    predicted = []

    for pattern in clinical_patterns[:3]:
        pattern_code = pattern_code_from_item(pattern)
        if pattern_code:
            predicted.append(pattern_code)

    return predicted


def extract_retrieved_sources(response_json: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []

    direct_sources = response_json.get("retrieved_sources")
    if isinstance(direct_sources, list):
        sources.extend([item for item in direct_sources if isinstance(item, dict)])

    dashboard = response_json.get("dashboard")
    if isinstance(dashboard, dict):
        dashboard_sources = dashboard.get("retrieved_sources")
        if isinstance(dashboard_sources, list):
            sources.extend([item for item in dashboard_sources if isinstance(item, dict)])

    clinical_patterns = extract_clinical_patterns(response_json)
    for pattern in clinical_patterns:
        pattern_code = pattern_code_from_item(pattern)
        nested_sources = pattern.get("retrieved_sources") or pattern.get("sources") or []

        if isinstance(nested_sources, list):
            for source in nested_sources:
                if isinstance(source, dict):
                    source_copy = dict(source)
                    if pattern_code and "pattern_code" not in source_copy:
                        source_copy["pattern_code"] = pattern_code
                    sources.append(source_copy)

    return sources


def has_safety_notice(response_json: dict[str, Any]) -> bool:
    possible_keys = [
        "safety_notice",
        "safetyNotice",
        "safety",
        "notice",
    ]

    for key in possible_keys:
        value = response_json.get(key)
        if isinstance(value, str) and value.strip():
            return True

    dashboard = response_json.get("dashboard")
    if isinstance(dashboard, dict):
        for key in possible_keys:
            value = dashboard.get(key)
            if isinstance(value, str) and value.strip():
                return True

    return False


def has_grounded_evidence_for_matched_patterns(
    matched_patterns: list[str],
    retrieved_sources: list[dict[str, Any]],
) -> bool:
    if not matched_patterns:
        return False

    if not retrieved_sources:
        return False

    sources_by_pattern: dict[str, list[dict[str, Any]]] = {}

    unassigned_sources = []

    for source in retrieved_sources:
        source_id = source.get("source_id")
        title = source.get("title")
        snippet = source.get("snippet") or source.get("chunk_text")

        has_useful_content = bool(source_id or title or snippet)
        if not has_useful_content:
            continue

        pattern_code = source.get("pattern_code")

        if pattern_code:
            sources_by_pattern.setdefault(str(pattern_code), []).append(source)
        else:
            unassigned_sources.append(source)

    for pattern in matched_patterns:
        if sources_by_pattern.get(pattern):
            continue

        # Fallback: if the response has useful retrieved sources but they are not
        # explicitly tagged with pattern_code, count the matched pattern as grounded.
        if unassigned_sources:
            continue

        return False

    return True


def evaluate_case(
    case: dict[str, Any],
    client: httpx.Client,
    analyze_url: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    case_id = case.get("id", "unknown")
    payload = case.get("input", {})
    expected_patterns = extract_expected_patterns(case)

    started_at = time.time()

    try:
        response = client.post(
            analyze_url,
            json=payload,
            timeout=timeout_seconds,
        )
        latency_ms = round((time.time() - started_at) * 1000, 2)

        response_json: dict[str, Any]
        try:
            response_json = response.json()
        except Exception:
            response_json = {"raw_response": response.text}

        if response.status_code >= 400:
            return {
                "case_id": case_id,
                "status": "error",
                "status_code": response.status_code,
                "expected_patterns": expected_patterns,
                "predicted_top3": [],
                "matched_patterns": [],
                "is_top3_correct": False,
                "is_evidence_grounded": False,
                "has_safety_notice": False,
                "latency_ms": latency_ms,
                "error": response_json,
            }

        predicted_top3 = extract_predicted_top3(response_json)
        matched_patterns = [
            pattern for pattern in expected_patterns if pattern in predicted_top3
        ]

        retrieved_sources = extract_retrieved_sources(response_json)

        is_top3_correct = len(matched_patterns) > 0
        is_evidence_grounded = has_grounded_evidence_for_matched_patterns(
            matched_patterns,
            retrieved_sources,
        )

        return {
            "case_id": case_id,
            "status": "ok",
            "status_code": response.status_code,
            "expected_patterns": expected_patterns,
            "predicted_top3": predicted_top3,
            "matched_patterns": matched_patterns,
            "is_top3_correct": is_top3_correct,
            "is_evidence_grounded": is_evidence_grounded,
            "has_safety_notice": has_safety_notice(response_json),
            "latency_ms": latency_ms,
            "report_case_id": response_json.get("report_case_id"),
            "retrieved_source_count": len(retrieved_sources),
        }

    except Exception as error:
        latency_ms = round((time.time() - started_at) * 1000, 2)

        return {
            "case_id": case_id,
            "status": "exception",
            "status_code": None,
            "expected_patterns": expected_patterns,
            "predicted_top3": [],
            "matched_patterns": [],
            "is_top3_correct": False,
            "is_evidence_grounded": False,
            "has_safety_notice": False,
            "latency_ms": latency_ms,
            "error": str(error),
        }


def calculate_metrics(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(case_results)

    if total_cases == 0:
        return {
            "total_cases": 0,
            "top3_clinical_pattern_recall": 0.0,
            "evidence_grounding_rate": 0.0,
            "average_latency_ms": 0.0,
            "safety_notice_presence_rate": 0.0,
        }

    completed_cases = [result for result in case_results if result["status"] == "ok"]
    error_cases = [result for result in case_results if result["status"] != "ok"]

    top3_correct_count = sum(1 for result in case_results if result["is_top3_correct"])
    grounded_count = sum(1 for result in case_results if result["is_evidence_grounded"])
    safety_notice_count = sum(1 for result in case_results if result["has_safety_notice"])

    average_latency_ms = round(
        sum(result["latency_ms"] for result in case_results) / total_cases,
        2,
    )

    status_distribution = Counter(result["status"] for result in case_results)

    return {
        "total_cases": total_cases,
        "completed_cases": len(completed_cases),
        "error_cases": len(error_cases),
        "status_distribution": dict(status_distribution),
        "top3_correct_count": top3_correct_count,
        "top3_clinical_pattern_recall": round(top3_correct_count / total_cases, 4),
        "evidence_grounded_count": grounded_count,
        "evidence_grounding_rate": round(grounded_count / total_cases, 4),
        "safety_notice_count": safety_notice_count,
        "safety_notice_presence_rate": round(safety_notice_count / total_cases, 4),
        "average_latency_ms": average_latency_ms,
    }


def run_eval(
    heldout_path: Path,
    output_path: Path,
    base_url: str,
    timeout_seconds: float,
    limit: int | None = None,
) -> dict[str, Any]:
    cases = load_jsonl(heldout_path)

    if limit is not None:
        cases = cases[:limit]

    analyze_url = f"{base_url.rstrip('/')}/reports/analyze"

    case_results = []

    with httpx.Client() as client:
        for index, case in enumerate(cases, start=1):
            case_id = case.get("id", f"case-{index}")
            print(f"[{index}/{len(cases)}] Evaluating {case_id}...")

            result = evaluate_case(
                case=case,
                client=client,
                analyze_url=analyze_url,
                timeout_seconds=timeout_seconds,
            )
            case_results.append(result)

            print(
                f"  status={result['status']} "
                f"top3={result['is_top3_correct']} "
                f"grounded={result['is_evidence_grounded']} "
                f"latency_ms={result['latency_ms']}"
            )

    metrics = calculate_metrics(case_results)

    output = {
        "base_url": base_url,
        "heldout_path": str(heldout_path),
        "metrics": metrics,
        "cases": case_results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output


def main():
    parser = argparse.ArgumentParser(description="Run held-out evaluation for MedDx Assistant.")
    parser.add_argument("--heldout", default=str(DEFAULT_HELDOUT_PATH))
    parser.add_argument("--output", default=str(DEFAULT_RESULTS_PATH))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    output = run_eval(
        heldout_path=Path(args.heldout),
        output_path=Path(args.output),
        base_url=args.base_url,
        timeout_seconds=args.timeout,
        limit=args.limit,
    )

    print("\nEvaluation complete.")
    print(json.dumps(output["metrics"], indent=2, ensure_ascii=False))
    print(f"\nSaved results to: {args.output}")


if __name__ == "__main__":
    main()