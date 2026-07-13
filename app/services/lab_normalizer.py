import json
import re
from difflib import get_close_matches
from pathlib import Path
from typing import Any


class LabNormalizer:
    def __init__(
        self,
        aliases_path: str = "data/lab_name_aliases.json",
        templates_path: str = "data/panel_templates.json",
    ):
        project_root = Path(__file__).resolve().parents[2]
        self.aliases_path = self._resolve_path(aliases_path, project_root)
        self.templates_path = self._resolve_path(templates_path, project_root)
        self.alias_map = self._load_aliases()
        self.known_symptoms = self._load_known_symptoms()

    def _resolve_path(self, raw_path: str, project_root: Path) -> Path:
        path = Path(raw_path)
        return path if path.is_absolute() else project_root / path

    def _clean_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower().strip())

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Required JSON file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a JSON object.")

        return data

    def _load_aliases(self) -> dict[str, str]:
        raw = self._load_json(self.aliases_path)
        aliases = raw.get("aliases") or raw.get("lab_name_aliases") or raw
        alias_map: dict[str, str] = {}

        if isinstance(aliases, dict):
            for canonical_name, alias_list in aliases.items():
                names = [canonical_name]

                if isinstance(alias_list, list):
                    names.extend(alias_list)
                elif isinstance(alias_list, str):
                    names.append(alias_list)

                for name in names:
                    alias_map[self._clean_key(str(name))] = str(canonical_name)

        elif isinstance(aliases, list):
            for item in aliases:
                if not isinstance(item, dict):
                    continue

                canonical_name = item.get("canonical") or item.get("name")
                alias_list = item.get("aliases", [])

                if not canonical_name:
                    continue

                for name in [canonical_name, *alias_list]:
                    alias_map[self._clean_key(str(name))] = str(canonical_name)

        return alias_map

    def _load_known_symptoms(self) -> set[str]:
        if not self.templates_path.exists():
            return set()

        raw = self._load_json(self.templates_path)
        collection = raw.get("panels") or raw.get("templates") or raw.get("panel_templates") or raw
        symptoms: set[str] = set()

        if isinstance(collection, dict):
            values = collection.values()
        elif isinstance(collection, list):
            values = collection
        else:
            values = []

        for panel in values:
            if not isinstance(panel, dict):
                continue

            for symptom in panel.get("suggested_symptoms", []):
                if isinstance(symptom, str) and symptom.strip():
                    symptoms.add(symptom.strip().lower())

        return symptoms

    def normalize_lab_name(self, lab_name: str) -> str:
        cleaned = self._clean_key(lab_name)
        return self.alias_map.get(cleaned, lab_name.strip())

    def normalize_symptom(self, symptom: str) -> str:
        normalized = symptom.strip().lower()

        if not normalized or normalized in self.known_symptoms:
            return normalized

        matches = get_close_matches(normalized, list(self.known_symptoms), n=1, cutoff=0.7)
        return matches[0] if matches else normalized

    def normalize_symptoms(self, symptoms: list[str]) -> list[str]:
        return [self.normalize_symptom(symptom) for symptom in symptoms if symptom.strip()]

    def normalize_labs(self, labs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_labs: list[dict[str, Any]] = []

        for lab in labs:
            lab_copy = dict(lab)
            original_name = lab_copy.get("name") or lab_copy.get("test_name")

            if not original_name:
                continue

            test_name = self.normalize_lab_name(str(original_name))
            lab_copy["original_name"] = str(original_name)
            lab_copy["name"] = test_name
            lab_copy["test_name"] = test_name
            normalized_labs.append(lab_copy)

        return normalized_labs


_DEFAULT_NORMALIZER: LabNormalizer | None = None


def _default_normalizer() -> LabNormalizer:
    global _DEFAULT_NORMALIZER

    if _DEFAULT_NORMALIZER is None:
        _DEFAULT_NORMALIZER = LabNormalizer()

    return _DEFAULT_NORMALIZER


def normalize_lab_name(name: str) -> str:
    return _default_normalizer().normalize_lab_name(name)


def normalize_symptom(text: str) -> str:
    return _default_normalizer().normalize_symptom(text)