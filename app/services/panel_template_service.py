import json
import re
from pathlib import Path
from typing import Any


class PanelTemplateService:
    def __init__(self, template_path: str = "data/panel_templates.json"):
        """
        Initialize the panel template service.

        The default path is data/panel_templates.json.
        The path is resolved from the project root so it works even if FastAPI
        is started from a different working directory.
        """

        raw_path = Path(template_path)

        if raw_path.is_absolute():
            self.template_path = raw_path
        else:
            project_root = Path(__file__).resolve().parents[2]
            self.template_path = project_root / raw_path

        self.templates = self._load_templates()
        self.lookup = self._build_lookup()

    def _load_json(self) -> dict[str, Any]:
        """
        Load the raw panel_templates.json file.
        """

        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Panel template file not found: {self.template_path}"
            )

        with self.template_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("panel_templates.json must contain a JSON object.")

        return data

    def _clean_key(self, value: str) -> str:
        """
        Normalize a string for flexible lookup.

        Examples:
        CBC_Panel -> cbcpanel
        CBC Panel -> cbcpanel
        Complete Blood Count (CBC) -> completebloodcountcbc
        """

        return re.sub(r"[^a-z0-9]+", "", value.lower().strip())

    def _display_name_from_key(self, key: str) -> str:
        """
        Convert an internal panel key into a readable display name.
        """

        return key.replace("_", " ").strip()

    def _test_to_object(self, test: Any) -> dict[str, Any] | None:
        """
        Normalize a test definition into a standard dictionary.

        Supports:
        - "Hemoglobin"
        - {"name": "Hemoglobin", "unit": "g/dL", "required": true}
        """

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
        """
        Convert each panel template into one consistent structure.

        Final structure:
        {
            "key": "CBC_Panel",
            "display_name": "Complete Blood Count (CBC)",
            "required_patient_fields": ["age", "sex", "symptoms"],
            "tests": [...],
            "suggested_symptoms": [...]
        }
        """

        if isinstance(value, list):
            tests = []

            for test in value:
                test_obj = self._test_to_object(test)
                if test_obj:
                    tests.append(test_obj)

            return {
                "key": key,
                "panel_name": key,
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
                "panel_name": key,
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
        """
        Load and normalize all panel templates.

        Important:
        The returned dictionary is keyed by the internal panel key,
        for example:
        {
            "CBC_Panel": {...},
            "Diabetic_Panel": {...}
        }
        """

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
                    or item.get("panel_name")
                    or item.get("name")
                    or item.get("display_name")
                    or f"panel_{index}"
                )

                template = self._normalize_template(key, item)

                if template:
                    templates[template["key"]] = template

        elif isinstance(collection, dict):
            for key, value in collection.items():
                template = self._normalize_template(key, value)

                if template:
                    templates[template["key"]] = template

        if not templates:
            raise ValueError("No valid panel templates were found.")

        return templates

    def _manual_aliases(self) -> dict[str, list[str]]:
        """
        Optional aliases for friendly panel lookup.

        This does not replace panel_templates.json.
        It only allows flexible calls like:
        /templates/CBC
        /templates/CBC Panel
        /templates/Complete Blood Count (CBC)
        """

        return {
            "CBC_Panel": [
                "CBC",
                "CBC Panel",
                "Complete Blood Count",
                "Complete Blood Count CBC",
            ],
            "Diabetic_Panel": [
                "Diabetic Panel",
                "Diabetic / Rapid Glucose Panel",
                "Diabetic & Glucose Panel",
                "Rapid Glucose Panel",
                "Glucose Panel",
            ],
            "Renal_Thyroid_Panel": [
                "Renal Thyroid Panel",
                "Renal & Thyroid Panel",
            ],
            "Lipids_Inflammation_Panel": [
                "Lipids Inflammation Panel",
                "Lipids & Inflammation Panel",
            ],
            "Cardiac_Enzymes_Panel": [
                "Cardiac Enzymes",
                "Cardiac Panel",
                "Cardiac Enzymes Panel",
            ],
            "Electrolytes_Calcium_Panel": [
                "Electrolytes Calcium Panel",
                "Electrolytes & Calcium Panel",
            ],
            "Albumin_Protein_Panel": [
                "Albumin Protein Panel",
                "Albumin & Protein Panel",
                "Protein Albumin Panel",
                "Protein / Albumin Panel",
            ],
        }

    def _build_lookup(self) -> dict[str, str]:
        """
        Build lookup map for panel names.

        The lookup supports:
        - internal key: CBC_Panel
        - display name: Complete Blood Count (CBC)
        - aliases: CBC, CBC Panel, etc.
        """

        lookup: dict[str, str] = {}

        for panel_key, template in self.templates.items():
            display_name = template.get("display_name", panel_key)

            candidates = {
                panel_key,
                display_name,
                panel_key.replace("_", " "),
                display_name.replace("_", " "),
                panel_key.replace(" ", "_"),
                display_name.replace(" ", "_"),
            }

            for candidate in candidates:
                lookup[self._clean_key(candidate)] = panel_key

        for panel_key, aliases in self._manual_aliases().items():
            if panel_key not in self.templates:
                continue

            lookup[self._clean_key(panel_key)] = panel_key

            for alias in aliases:
                lookup[self._clean_key(alias)] = panel_key

        return lookup

    def _template_words(self, template: dict[str, Any]) -> str:
        """
        Build searchable words from a template.

        Used as fallback if the panel was not found in the lookup.
        """

        key = template.get("key", "")
        display_name = template.get("display_name", "")

        tests = " ".join(
            test.get("name", "")
            for test in template.get("tests", [])
            if isinstance(test, dict)
        )

        return self._clean_key(f"{key} {display_name} {tests}")

    def _find_template_by_words(self, panel_name: str) -> str | None:
        """
        Fallback search for a panel using words from:
        - key
        - display_name
        - test names
        """

        wanted = self._clean_key(panel_name)

        for panel_key, template in self.templates.items():
            words = self._template_words(template)

            if wanted in words or words in wanted:
                return panel_key

            if "cardiac" in wanted and any(
                x in words for x in ["cardiac", "troponin", "cpk", "ck"]
            ):
                return panel_key

            if "cbc" in wanted and any(
                x in words for x in ["cbc", "hemoglobin", "wbc", "platelets"]
            ):
                return panel_key

            if "diabetic" in wanted or "glucose" in wanted:
                if any(x in words for x in ["diabetic", "glucose", "hba1c"]):
                    return panel_key

            if "renal" in wanted or "thyroid" in wanted:
                if any(x in words for x in ["renal", "thyroid", "creatinine", "tsh"]):
                    return panel_key

            if "lipids" in wanted or "inflammation" in wanted:
                if any(x in words for x in ["lipids", "inflammation", "ldl", "hdl", "crp"]):
                    return panel_key

            if "electrolytes" in wanted or "calcium" in wanted:
                if any(x in words for x in ["electrolytes", "calcium", "sodium", "potassium"]):
                    return panel_key

            if "albumin" in wanted or "protein" in wanted:
                if any(x in words for x in ["albumin", "protein"]):
                    return panel_key

        return None

    def get_available_panels(self) -> list[dict[str, Any]]:
        """
        Return a lightweight list of available panels.

        This is useful for:
        - GET /templates
        - Gradio dropdown
        """

        panels: list[dict[str, Any]] = []

        for panel_key, template in self.templates.items():
            required_tests = [
                test["name"]
                for test in template.get("tests", [])
                if isinstance(test, dict) and test.get("required", True)
            ]

            panels.append(
                {
                    "panel_name": panel_key,
                    "display_name": template.get("display_name", panel_key),
                    "required_tests": required_tests,
                }
            )

        return panels

    def get_all_templates(self) -> list[dict[str, Any]]:
        """
        Return all normalized templates.
        """

        return list(self.templates.values())

    def get_template(self, panel_name: str) -> dict[str, Any] | None:
        """
        Return a specific panel template.

        Supports:
        - CBC_Panel
        - CBC Panel
        - Complete Blood Count (CBC)
        """

        cleaned = self._clean_key(panel_name)
        panel_key = self.lookup.get(cleaned)

        if panel_key:
            return self.templates[panel_key]

        fallback_panel_key = self._find_template_by_words(panel_name)

        if fallback_panel_key:
            return self.templates[fallback_panel_key]

        return None

    def get_required_test_names(self, panel_name: str) -> list[str]:
        """
        Return required test names for a selected panel.
        """

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
        """
        Find missing required labs for a selected panel.

        This function is designed to be used later inside /reports/analyze.

        Example:
        Required for CBC_Panel:
        ["Hemoglobin", "WBC", "Platelets"]

        Submitted:
        ["Hemoglobin", "WBC"]

        Output:
        ["Platelets"]
        """

        required = self.get_required_test_names(panel_name)

        if not required:
            return []

        normalized_submitted = {
            normalizer.normalize_lab_name(name)
            for name in submitted_lab_names
            if name
        }

        missing: list[str] = []

        for required_name in required:
            normalized_required = normalizer.normalize_lab_name(required_name)

            if normalized_required not in normalized_submitted:
                missing.append(required_name)

        return missing