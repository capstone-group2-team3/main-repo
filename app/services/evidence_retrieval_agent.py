import json
import os
import re
from pathlib import Path
from typing import Any

from app.services.embedding_service import EmbeddingService


class EvidenceRetrievalAgent:
    """Panel-aware retrieval with metadata filtering and deterministic validation."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        collection_name: str = "medical_knowledge",
        qdrant_url: str | None = None,
        minimum_similarity: float = 0.2,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.minimum_similarity = minimum_similarity
        self.client = None
        project_root = Path(__file__).resolve().parents[2]
        aliases_path = project_root / "data" / "lab_name_aliases.json"
        self.lab_aliases = json.loads(aliases_path.read_text(encoding="utf-8"))

    def _get_qdrant_client(self):
        if self.client is None:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(url=self.qdrant_url)
        return self.client

    def _normalize(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

    def _aliases_for(self, lab_name: str) -> set[str]:
        aliases = self.lab_aliases.get(lab_name, [])
        return {self._normalize(item) for item in [lab_name, *aliases] if self._normalize(item)}

    def _contains_term(self, text: str, term: str) -> bool:
        normalized = f" {self._normalize(text)} "
        wanted = self._normalize(term)
        return bool(wanted and f" {wanted} " in normalized)

    def _abnormal_lab_names(self, abnormal_labs: list[dict[str, Any]] | None, pattern: dict[str, Any]) -> list[str]:
        evidence = " ".join(map(str, pattern.get("evidence_for", [])))
        evidence_names = {name for name in self.lab_aliases if any(self._contains_term(evidence, alias) for alias in self._aliases_for(name))}
        submitted_names = {str(item.get("test_name") or item.get("name") or item.get("test")) for item in abnormal_labs or [] if item.get("test_name") or item.get("name") or item.get("test")}
        matched = submitted_names.intersection(evidence_names)
        return sorted(matched or evidence_names or submitted_names)

    def _lab_direction(self, lab: dict[str, Any]) -> str:
        status = self._normalize(lab.get("status")).replace(" ", "_")
        if status in {"high", "low", "normal", "critical_high", "critical_low"}:
            return status
        if status == "critical":
            try:
                value = float(lab.get("value"))
            except (TypeError, ValueError):
                return "unknown"
            critical_low = lab.get("critical_low")
            reference_low = lab.get("reference_low")
            critical_high = lab.get("critical_high")
            reference_high = lab.get("reference_high")
            if critical_low is not None and value <= float(critical_low):
                return "critical_low"
            if critical_high is not None and value >= float(critical_high):
                return "critical_high"
            if reference_low is not None and value < float(reference_low):
                return "critical_low"
            if reference_high is not None and value > float(reference_high):
                return "critical_high"
        return status or "unknown"

    def _lab_directions(self, abnormal_labs: list[dict[str, Any]] | None, target_names: list[str]) -> dict[str, str]:
        directions = {}
        for lab in abnormal_labs or []:
            name = str(lab.get("test_name") or lab.get("name") or lab.get("test") or "")
            if name in target_names:
                directions[name] = self._lab_direction(lab)
        return directions

    def _direction_compatible(self, source_direction: str, target_directions: set[str]) -> bool:
        source = self._normalize(source_direction).replace(" ", "_") or "unknown"
        if source in {"general", "unknown"} or not target_directions:
            return True
        high = {"high", "critical_high"}
        low = {"low", "critical_low"}
        if target_directions.intersection(high) and source in low:
            return False
        if target_directions.intersection(low) and source in high:
            return False
        if "normal" in target_directions and source in high.union(low).union({"abnormal"}):
            return False
        if "abnormal" in target_directions and source == "normal":
            return False
        return True

    def build_query(
        self,
        pattern: dict[str, Any],
        selected_panel: str | None = None,
        abnormal_labs: list[dict[str, Any]] | None = None,
        symptoms: list[str] | None = None,
    ) -> str:
        lab_parts = []
        lab_names = self._abnormal_lab_names(abnormal_labs, pattern)
        status_by_name = {
            str(item.get("test_name") or item.get("name") or item.get("test")): str(item.get("status") or "abnormal")
            for item in abnormal_labs or []
        }
        for name in lab_names:
            lab_parts.append(f"{status_by_name.get(name, 'abnormal')} {name}")
        aliases = sorted({alias for name in lab_names for alias in self._aliases_for(name)})
        parts = [
            f"Panel {selected_panel}" if selected_panel else "",
            ". ".join(lab_parts),
            str(pattern.get("pattern_name") or ""),
            str(pattern.get("pattern_code") or ""),
            f"Symptoms {', '.join(symptoms or [])}" if symptoms else "",
            f"Terms: {', '.join(aliases)}" if aliases else "",
        ]
        return ". ".join(part for part in parts if part).strip()

    def _panel_filter(self, selected_panel: str | None):
        if not selected_panel:
            return None
        from qdrant_client.http import models
        return models.Filter(must=[models.FieldCondition(key="canonical_panel", match=models.MatchValue(value=selected_panel))])

    def _search(self, query_vector: list[float], limit: int, selected_panel: str | None) -> list[Any]:
        client = self._get_qdrant_client()
        query_filter = self._panel_filter(selected_panel)
        try:
            response = client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            return list(response.points if hasattr(response, "points") else response)
        except (AttributeError, TypeError):
            response = client.search_points(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            return list(response.points if hasattr(response, "points") else response)

    def clean_snippet(self, text: str | None) -> str:
        cleaned_lines = []
        for line in str(text or "").splitlines():
            line = re.sub(r"^\s*#{1,6}\s*", "", line)
            line = re.sub(r"^\s*[-*+]\s+", "", line)
            line = line.strip()
            if line and line != "---":
                cleaned_lines.append(line)
        return re.sub(r"\s+", " ", " ".join(cleaned_lines)).strip()

    def is_candidate_relevant(
        self,
        payload: dict[str, Any],
        similarity: float,
        selected_panel: str | None,
        abnormal_labs: list[str],
        lab_directions: dict[str, str],
        pattern: dict[str, Any],
    ) -> bool:
        if similarity < self.minimum_similarity:
            return False
        candidate_panel = payload.get("canonical_panel")
        related_tests = {str(item) for item in payload.get("related_tests", [])}
        pattern_codes = {str(item) for item in payload.get("pattern_codes", [])}
        pattern_code = str(pattern.get("pattern_code") or "")
        target_tests = set(abnormal_labs)
        target_directions = {direction for name, direction in lab_directions.items() if name in target_tests}
        source_direction = str(payload.get("status_direction") or "unknown")
        direct_test_match = bool(target_tests.intersection(related_tests))
        pattern_match = bool(pattern_code and pattern_code in pattern_codes)
        lexical_text = " ".join([
            str(payload.get("section_title") or ""),
            str(payload.get("chunk_text") or ""),
            " ".join(map(str, payload.get("normalized_terms", []))),
        ])
        lexical_match = any(any(self._contains_term(lexical_text, alias) for alias in self._aliases_for(test)) for test in target_tests)

        if selected_panel and candidate_panel and candidate_panel != selected_panel and not (direct_test_match or pattern_match):
            return False
        if related_tests and target_tests and not direct_test_match and not pattern_match:
            return False
        if target_tests and not (direct_test_match or pattern_match or lexical_match):
            return False
        if not self._direction_compatible(source_direction, target_directions):
            return False
        if source_direction == "general" and target_tests and not (direct_test_match or pattern_match or lexical_match):
            return False
        if not candidate_panel and not (direct_test_match or pattern_match or lexical_match):
            return False
        return True

    def _relevance_score(
        self,
        payload: dict[str, Any],
        similarity: float,
        selected_panel: str | None,
        abnormal_labs: list[str],
        lab_directions: dict[str, str],
        pattern: dict[str, Any],
    ) -> float:
        score = float(similarity)
        related = set(map(str, payload.get("related_tests", [])))
        codes = set(map(str, payload.get("pattern_codes", [])))
        section = str(payload.get("section_title") or "")
        if selected_panel and payload.get("canonical_panel") == selected_panel:
            score += 0.25
        if set(abnormal_labs).intersection(related):
            score += 0.35
        if pattern.get("pattern_code") in codes:
            score += 0.25
        if any(any(self._contains_term(section, alias) for alias in self._aliases_for(test)) for test in abnormal_labs):
            score += 0.15
        source_direction = str(payload.get("status_direction") or "unknown")
        target_directions = set(lab_directions.values())
        if source_direction in target_directions:
            score += 0.2
        elif source_direction == "general":
            score += 0.05
        return round(score, 6)

    def retrieve_for_pattern(
        self,
        pattern: dict[str, Any],
        top_k: int = 3,
        selected_panel: str | None = None,
        abnormal_labs: list[dict[str, Any]] | None = None,
        symptoms: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        lab_names = self._abnormal_lab_names(abnormal_labs, pattern)
        lab_directions = self._lab_directions(abnormal_labs, lab_names)
        query_vector = self.embedding_service.embed_text(self.build_query(pattern, selected_panel, abnormal_labs, symptoms))
        candidate_limit = max(top_k * 5, 10)
        candidates = self._search(query_vector, candidate_limit, selected_panel)
        ranked = []
        for hit in candidates:
            payload = dict(getattr(hit, "payload", {}) or {})
            similarity = float(getattr(hit, "score", 0.0) or 0.0)
            if not self.is_candidate_relevant(payload, similarity, selected_panel, lab_names, lab_directions, pattern):
                continue
            ranked.append((self._relevance_score(payload, similarity, selected_panel, lab_names, lab_directions, pattern), payload, similarity))

        # Older indexes may not have canonical_panel. A relaxed pass is allowed,
        # but the same lexical/test/pattern validation still applies.
        if not ranked and selected_panel:
            for hit in self._search(query_vector, candidate_limit, None):
                payload = dict(getattr(hit, "payload", {}) or {})
                similarity = float(getattr(hit, "score", 0.0) or 0.0)
                if self.is_candidate_relevant(payload, similarity, selected_panel, lab_names, lab_directions, pattern):
                    ranked.append((self._relevance_score(payload, similarity, selected_panel, lab_names, lab_directions, pattern), payload, similarity))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "source_id": payload.get("source_id"),
                "title": payload.get("title"),
                "snippet": self.clean_snippet(payload.get("chunk_text")),
                "similarity_score": similarity,
                "relevance_score": score,
                "canonical_panel": payload.get("canonical_panel"),
                "related_tests": payload.get("related_tests", []),
                "section_title": payload.get("section_title"),
                "status_direction": payload.get("status_direction"),
            }
            for score, payload, similarity in ranked[:top_k]
        ]

    def retrieve_for_patterns(
        self,
        patterns: list[dict[str, Any]],
        top_k: int = 3,
        selected_panel: str | None = None,
        abnormal_labs: list[dict[str, Any]] | None = None,
        symptoms: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "pattern_code": pattern.get("pattern_code"),
                "retrieved_sources": self.retrieve_for_pattern(pattern, top_k, selected_panel, abnormal_labs, symptoms),
            }
            for pattern in patterns
        ]
