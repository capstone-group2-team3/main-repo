import json
import re
from pathlib import Path
from typing import Any


DATA_DIR = Path("data")
JSON_FILES = sorted(DATA_DIR.rglob("*.json"))
JSONL_FILES = sorted(DATA_DIR.rglob("*.jsonl"))
DATE_KEY_RE = re.compile(r"(date|time|created_at|indexed_at|generated_at|timestamp)$", re.I)
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?")
NUMERIC_RANGE_KEYS = {
    "min",
    "max",
    "low",
    "high",
    "reference_low",
    "reference_high",
    "normal_low",
    "normal_high",
    "critical_low",
    "critical_high",
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen = set()
    result = {}

    for key, value in pairs:
        assert key not in seen, f"Duplicate JSON key: {key}"
        seen.add(key)
        result[key] = value

    return result


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _assert_config_values(path: Path, value: Any):
    for item in _walk(value):
        for key, field_value in item.items():
            if key in NUMERIC_RANGE_KEYS and field_value is not None:
                assert isinstance(field_value, (int, float)), f"{path}: {key} must be numeric or null"

            if DATE_KEY_RE.search(key) and field_value is not None:
                assert isinstance(field_value, str), f"{path}: {key} must be an ISO string"
                assert ISO_RE.match(field_value), f"{path}: {key} must be ISO formatted"


def test_data_json_files_are_valid_and_well_formed():
    assert JSON_FILES

    for path in JSON_FILES:
        value = _load_json(path)
        _assert_config_values(path, value)


def test_data_jsonl_files_are_valid_and_well_formed():
    assert JSONL_FILES

    for path in JSONL_FILES:
        lines = path.read_text(encoding="utf-8").splitlines()

        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
            try:
                _assert_config_values(path, value)
            except AssertionError as error:
                raise AssertionError(f"{path}:{line_number}: {error}") from error
