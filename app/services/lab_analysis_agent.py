import json
from pathlib import Path
from typing import Any

from app.services.lab_normalizer import LabNormalizer


class LabAnalysisAgent:
    def __init__(
        self,
        ranges_path: str = "data/reference_ranges.json",
        normalizer: LabNormalizer | None = None,
    ):
        self.ranges_path = Path(ranges_path)
        self.normalizer = normalizer or LabNormalizer()
        self.reference_ranges = self._load_reference_ranges()

    def _load_json(self) -> dict[str, Any]:
        if not self.ranges_path.exists():
            raise FileNotFoundError(f"Reference ranges file not found: {self.ranges_path}")

        with self.ranges_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _has_range_keys(self, item: dict[str, Any]) -> bool:
        range_keys = {
            "low",
            "high",
            "reference_low",
            "reference_high",
            "normal_low",
            "normal_high",
            "critical_low",
            "critical_high",
            "min",
            "max",
        }
        return any(key in item for key in range_keys) or isinstance(item.get("reference_range"), dict)

    def _first_present(self, *values: Any) -> Any:
        for value in values:
            if value is not None:
                return value
        return None

    def _extract_range(self, item: dict[str, Any]) -> dict[str, Any]:
        reference_range = item.get("reference_range", {})

        if not isinstance(reference_range, dict):
            reference_range = {}

        return {
            "unit": item.get("unit"),
            "reference_low": self._first_present(
                item.get("reference_low"),
                item.get("normal_low"),
                item.get("low"),
                item.get("min"),
                reference_range.get("low"),
                reference_range.get("min"),
            ),
            "reference_high": self._first_present(
                item.get("reference_high"),
                item.get("normal_high"),
                item.get("high"),
                item.get("max"),
                reference_range.get("high"),
                reference_range.get("max"),
            ),
            "critical_low": item.get("critical_low"),
            "critical_high": item.get("critical_high"),
        }

    def _load_reference_ranges(self) -> dict[str, dict[str, Any]]:
        raw = self._load_json()
        root = raw.get("ranges") or raw.get("reference_ranges") or raw

        ranges: dict[str, dict[str, Any]] = {}

        def visit(obj: Any, parent_key: str | None = None):
            if isinstance(obj, dict):
                if self._has_range_keys(obj) and parent_key:
                    canonical = self.normalizer.normalize_lab_name(parent_key)
                    ranges[canonical] = self._extract_range(obj)
                    return

                tests = obj.get("tests")
                if isinstance(tests, list):
                    for test in tests:
                        if not isinstance(test, dict):
                            continue
                        name = test.get("name") or test.get("test_name") or test.get("display_name")
                        if name and self._has_range_keys(test):
                            canonical = self.normalizer.normalize_lab_name(name)
                            ranges[canonical] = self._extract_range(test)

                elif isinstance(tests, dict):
                    for name, test in tests.items():
                        if isinstance(test, dict) and self._has_range_keys(test):
                            canonical = self.normalizer.normalize_lab_name(name)
                            ranges[canonical] = self._extract_range(test)

                for key, value in obj.items():
                    if key == "tests":
                        continue
                    visit(value, key)

            elif isinstance(obj, list):
                for item in obj:
                    if not isinstance(item, dict):
                        continue

                    name = item.get("name") or item.get("test_name") or item.get("display_name")
                    if name and self._has_range_keys(item):
                        canonical = self.normalizer.normalize_lab_name(name)
                        ranges[canonical] = self._extract_range(item)

                    visit(item, name)

        visit(root)

        return ranges

    def _to_float_or_none(self, value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _classify_value(self, value: float, ref: dict[str, Any] | None) -> str:
        if not ref:
            return "Unknown"

        reference_low = self._to_float_or_none(ref.get("reference_low"))
        reference_high = self._to_float_or_none(ref.get("reference_high"))
        critical_low = self._to_float_or_none(ref.get("critical_low"))
        critical_high = self._to_float_or_none(ref.get("critical_high"))

        if critical_low is not None and value <= critical_low:
            return "Critical"
        if critical_high is not None and value >= critical_high:
            return "Critical"
        if reference_low is not None and value < reference_low:
            return "Low"
        if reference_high is not None and value > reference_high:
            return "High"
        if reference_low is not None or reference_high is not None:
            return "Normal"

        return "Unknown"

    def _build_evidence(self, test_name: str, value: float, unit: str | None, status: str, ref: dict[str, Any] | None) -> str:
        display_unit = unit or (ref or {}).get("unit") or ""

        if status == "Unknown":
            return f"No configured reference range was found for {test_name}."

        reference_low = ref.get("reference_low") if ref else None
        reference_high = ref.get("reference_high") if ref else None

        range_text = f"{reference_low}–{reference_high}".replace("None", "unknown")

        if status == "Normal":
            return f"{test_name} value {value} {display_unit} is within the configured educational reference range ({range_text})."

        return f"{test_name} value {value} {display_unit} is {status} compared with the configured educational reference range ({range_text})."

    def analyze_labs(self, selected_panel: str, labs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        analyzed_results: list[dict[str, Any]] = []

        for lab in labs:
            raw_name = lab.get("test_name") or lab.get("name")
            test_name = self.normalizer.normalize_lab_name(raw_name)
            value = float(lab["value"])
            ref = self.reference_ranges.get(test_name)
            status = self._classify_value(value, ref)

            unit = lab.get("unit") or (ref or {}).get("unit")

            analyzed_results.append(
                {
                    "panel": selected_panel,
                    "test_name": test_name,
                    "value": value,
                    "unit": unit,
                    "status": status,
                    "reference_low": self._to_float_or_none((ref or {}).get("reference_low")),
                    "reference_high": self._to_float_or_none((ref or {}).get("reference_high")),
                    "critical_low": self._to_float_or_none((ref or {}).get("critical_low")),
                    "critical_high": self._to_float_or_none((ref or {}).get("critical_high")),
                    "evidence": self._build_evidence(test_name, value, unit, status, ref),
                }
            )

        return analyzed_results
