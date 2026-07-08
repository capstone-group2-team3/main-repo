import json
import re
from pathlib import Path
from typing import Any


class LabNormalizer:
    def __init__(self, aliases_path: str = "data/lab_name_aliases.json"):
        self.aliases_path = Path(aliases_path)
        self.alias_map = self._load_aliases()

    def _clean_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower().strip())

    def _load_json(self) -> dict[str, Any]:
        if not self.aliases_path.exists():
            raise FileNotFoundError(f"Lab aliases file not found: {self.aliases_path}")

        with self.aliases_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_aliases(self) -> dict[str, str]:
        raw = self._load_json()

        aliases = (
            raw.get("aliases")
            or raw.get("lab_name_aliases")
            or raw
        )

        alias_map: dict[str, str] = {}

        if isinstance(aliases, dict):
            for canonical_name, alias_list in aliases.items():
                names = [canonical_name]

                if isinstance(alias_list, list):
                    names.extend(alias_list)
                elif isinstance(alias_list, str):
                    names.append(alias_list)

                for name in names:
                    alias_map[self._clean_key(name)] = canonical_name

        elif isinstance(aliases, list):
            for item in aliases:
                if not isinstance(item, dict):
                    continue

                canonical_name = item.get("canonical") or item.get("name")
                alias_list = item.get("aliases", [])

                if not canonical_name:
                    continue

                for name in [canonical_name, *alias_list]:
                    alias_map[self._clean_key(name)] = canonical_name

        return alias_map

    def normalize_lab_name(self, lab_name: str) -> str:
        cleaned = self._clean_key(lab_name)
        return self.alias_map.get(cleaned, lab_name.strip())

    def normalize_symptom(self, symptom: str) -> str:
        return symptom.strip().lower()

    def normalize_symptoms(self, symptoms: list[str]) -> list[str]:
        return [self.normalize_symptom(symptom) for symptom in symptoms if symptom.strip()]

    def normalize_labs(self, labs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_labs: list[dict[str, Any]] = []

        for lab in labs:
            lab_copy = dict(lab)
            original_name = lab_copy.get("name") or lab_copy.get("test_name")

            if not original_name:
                continue

            lab_copy["original_name"] = original_name
            lab_copy["name"] = self.normalize_lab_name(original_name)
            normalized_labs.append(lab_copy)

        return normalized_labs
