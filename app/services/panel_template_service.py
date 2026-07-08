import json
import re
from pathlib import Path
from typing import Any


class PanelTemplateService:
    def __init__(self, template_path: str = "data/panel_templates.json"):
        self.template_path = Path(template_path)
        self.templates = self._load_templates()
        self.lookup = self._build_lookup()

    def _load_json(self) -> dict[str, Any]:
        if not self.template_path.exists():
            raise FileNotFoundError(f"Panel template file not found: {self.template_path}")

        with self.template_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _clean_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower().strip())

    def _display_name_from_key(self, key: str) -> str:
        return key.replace("_", " ").strip()

    def _test_to_object(self, test: Any) -> dict[str, Any] | None:
        if isinstance(test, str):
            return {
                "name": test,
                "unit": None,
                "required": True,
                "description": "",
            }

        if isinstance(test, dict):
            name = (
                test.get("name")
                or test.get("test_name")
                or test.get("display_name")
                or test.get("field_name")
            )

            if not name:
                return None

            return {
                "name": name,
                "unit": test.get("unit"),
                "required": test.get("required", True),
                "description": test.get("description", ""),
            }

        return None

    def _normalize_template(self, key: str, value: Any) -> dict[str, Any] | None:
        if isinstance(value, list):
            tests = []
            for test in value:
                test_obj = self._test_to_object(test)
                if test_obj:
                    tests.append(test_obj)

            return {
                "key": key,
                "display_name": self._display_name_from_key(key),
                "required_patient_fields": ["age", "sex", "symptoms"],
                "tests": tests,
                "suggested_symptoms": [],
            }

        if isinstance(value, dict):
            display_name = (
                value.get("display_name")
                or value.get("panel_name")
                or value.get("name")
                or self._display_name_from_key(key)
            )

            raw_tests = value.get("tests", [])

            if isinstance(raw_tests, dict):
                iterable_tests = [
                    {"name": test_name, **test_data}
                    if isinstance(test_data, dict)
                    else test_name
                    for test_name, test_data in raw_tests.items()
                ]
            else:
                iterable_tests = raw_tests

            tests = []
            for test in iterable_tests:
                test_obj = self._test_to_object(test)
                if test_obj:
                    tests.append(test_obj)

            return {
                "key": key,
                "display_name": display_name,
                "required_patient_fields": value.get(
                    "required_patient_fields",
                    ["age", "sex", "symptoms"],
                ),
                "tests": tests,
                "suggested_symptoms": value.get("suggested_symptoms", []),
            }

        return None

    def _load_templates(self) -> dict[str, dict[str, Any]]:
        raw = self._load_json()

        collection = (
            raw.get("panels")
            or raw.get("templates")
            or raw.get("panel_templates")
            or raw
        )

        templates: dict[str, dict[str, Any]] = {}

        if isinstance(collection, list):
            for index, item in enumerate(collection):
                if not isinstance(item, dict):
                    continue

                key = (
                    item.get("key")
                    or item.get("display_name")
                    or item.get("panel_name")
                    or item.get("name")
                    or f"panel_{index}"
                )

                template = self._normalize_template(key, item)
                if template:
                    templates[template["display_name"]] = template

        elif isinstance(collection, dict):
            for key, value in collection.items():
                template = self._normalize_template(key, value)
                if template:
                    templates[template["display_name"]] = template

        return templates

    def _manual_aliases(self) -> dict[str, list[str]]:
        return {
            "CBC Panel": ["CBC_Panel", "CBC"],
            "Diabetic / Rapid Glucose Panel": [
                "Diabetic_Panel",
                "Diabetic Panel",
                "Rapid Glucose Panel",
                "Glucose Panel",
            ],
            "Renal & Thyroid Panel": [
                "Renal_Thyroid_Panel",
                "Renal Thyroid Panel",
            ],
            "Lipids & Inflammation Panel": [
                "Lipids_Inflammation_Panel",
                "Lipids Inflammation Panel",
            ],
            "Cardiac Enzymes Panel": [
                "Cardiac_Enzymes_Panel",
                "Cardiac Enzymes",
                "Cardiac_Panel",
                "Cardiac Panel",
            ],
            "Electrolytes & Calcium Panel": [
                "Electrolytes_Calcium_Panel",
                "Electrolytes Calcium Panel",
            ],
            "Coagulation Panel": ["Coagulation_Panel"],
            "Protein / Albumin Panel": [
                "Albumin_Protein_Panel",
                "Albumin Protein Panel",
                "Albumin / Protein Panel",
            ],
            "Pancreatic / Salivary Enzyme Panel": [
                "Pancreatic_Salivary_Panel",
                "Pancreatic_Salivary_Enzymes_Panel",
                "Pancreatic Salivary Enzymes Panel",
                "Amylase Panel",
            ],
        }

    def _build_lookup(self) -> dict[str, str]:
        lookup: dict[str, str] = {}

        for display_name, template in self.templates.items():
            key = template.get("key", display_name)

            candidates = {
                display_name,
                key,
                display_name.replace("_", " "),
                key.replace("_", " "),
                display_name.replace(" ", "_"),
                key.replace(" ", "_"),
            }

            for candidate in candidates:
                lookup[self._clean_key(candidate)] = display_name

        for public_name, aliases in self._manual_aliases().items():
            resolved_template = self._find_template_by_words(public_name)

            if resolved_template:
                lookup[self._clean_key(public_name)] = resolved_template

                for alias in aliases:
                    lookup[self._clean_key(alias)] = resolved_template

        return lookup

    def _template_words(self, template: dict[str, Any]) -> str:
        key = template.get("key", "")
        display_name = template.get("display_name", "")
        tests = " ".join(
            test.get("name", "")
            for test in template.get("tests", [])
            if isinstance(test, dict)
        )
        return self._clean_key(f"{key} {display_name} {tests}")

    def _find_template_by_words(self, panel_name: str) -> str | None:
        wanted = self._clean_key(panel_name)

        for display_name, template in self.templates.items():
            words = self._template_words(template)

            if wanted in words or words in wanted:
                return display_name

            if "cardiac" in wanted and any(x in words for x in ["cardiac", "troponin", "cpk", "ck"]):
                return display_name

            if "cbc" in wanted and any(x in words for x in ["cbc", "hemoglobin", "wbc", "platelets"]):
                return display_name

            if "diabetic" in wanted or "glucose" in wanted:
                if any(x in words for x in ["diabetic", "glucose", "hba1c"]):
                    return display_name

            if "renal" in wanted or "thyroid" in wanted:
                if any(x in words for x in ["renal", "thyroid", "creatinine", "tsh"]):
                    return display_name

            if "lipids" in wanted or "inflammation" in wanted:
                if any(x in words for x in ["lipids", "inflammation", "ldl", "hdl", "crp"]):
                    return display_name

            if "electrolytes" in wanted or "calcium" in wanted:
                if any(x in words for x in ["electrolytes", "calcium", "sodium", "potassium"]):
                    return display_name

            if "coagulation" in wanted:
                if any(x in words for x in ["coagulation", "pt", "ptt", "inr"]):
                    return display_name

            if "albumin" in wanted or "protein" in wanted:
                if any(x in words for x in ["albumin", "protein"]):
                    return display_name

            if "pancreatic" in wanted or "salivary" in wanted or "amylase" in wanted:
                if any(x in words for x in ["pancreatic", "salivary", "amylase"]):
                    return display_name

        return None

    def get_available_panels(self) -> list[str]:
        return list(self.templates.keys())

    def get_all_templates(self) -> list[dict[str, Any]]:
        return list(self.templates.values())

    def get_template(self, panel_name: str) -> dict[str, Any] | None:
        cleaned = self._clean_key(panel_name)
        display_name = self.lookup.get(cleaned)

        if display_name:
            return self.templates[display_name]

        fallback_display_name = self._find_template_by_words(panel_name)

        if fallback_display_name:
            return self.templates[fallback_display_name]

        return None

    def get_required_test_names(self, panel_name: str) -> list[str]:
        template = self.get_template(panel_name)

        if not template:
            return []

        required_names: list[str] = []

        for test in template.get("tests", []):
            if not isinstance(test, dict):
                continue

            if test.get("required", True) and test.get("name"):
                required_names.append(test["name"])

        return required_names

    def find_missing_required_labs(
        self,
        panel_name: str,
        submitted_lab_names: list[str],
        normalizer,
    ) -> list[str]:
        required = self.get_required_test_names(panel_name)

        normalized_submitted = {
            normalizer.normalize_lab_name(name) for name in submitted_lab_names
        }

        missing: list[str] = []

        for required_name in required:
            normalized_required = normalizer.normalize_lab_name(required_name)
            if normalized_required not in normalized_submitted:
                missing.append(required_name)

        return missing
