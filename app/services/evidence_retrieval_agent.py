# app/services/evidence_retrieval_agent.py

from app.services.embedding_service import EmbeddingService


class EvidenceRetrievalAgent:
    """
    EvidenceRetrievalAgent is responsible for retrieving relevant evidence from a vector database (Qdrant) based on clinical pattern results."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        collection_name: str = "medical_knowledge",
        qdrant_url: str | None = None,
    ):
        import os
        self.embedding_service = embedding_service or EmbeddingService()
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = None

    def _get_qdrant_client(self):
        if self.client is not None:
            return self.client
        from qdrant_client import QdrantClient
        self.client = QdrantClient(url=self.qdrant_url)
        return self.client

    def build_query(self, pattern: dict) -> str:
        """
        Build a query string for a given clinical pattern result."""
        pattern_name = pattern.get("pattern_name", "")
        evidence = pattern.get("evidence_for", [])
        evidence_text = " ".join(evidence)
        return f"{pattern_name} {evidence_text}".strip()

    def retrieve_for_pattern(self, pattern: dict, top_k: int = 3) -> list[dict]:
        """
        Retrieve evidence for a single clinical pattern result.
        """
        query_text = self.build_query(pattern)
        query_vector = self.embedding_service.embed_text(query_text)

        client = self._get_qdrant_client()
        
        try:
            # Try search_points API (qdrant-client >= 1.7.0)
            search_result = client.search_points(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
            )
            # Handle both direct list and object with .points attribute
            results = search_result.points if hasattr(search_result, 'points') else search_result
        except (AttributeError, TypeError) as e1:
            try:
                # Try query API (older versions)
                results = client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=top_k,
                ).points
            except (AttributeError, TypeError) as e2:
                print(f"Warning: Could not search Qdrant with search_points or query: {e1}, {e2}")
                print(f"Available methods: {[m for m in dir(client) if not m.startswith('_')]}")
                return []

        retrieved_sources = []
        for hit in results:
            retrieved_sources.append({
                "source_id": hit.payload.get("source_id"),
                "title": hit.payload.get("title"),
                "snippet": hit.payload.get("chunk_text"),
                "similarity_score": hit.score,
            })

        return retrieved_sources

    def retrieve_for_patterns(self, patterns: list[dict], top_k: int = 3) -> list[dict]:
        """
        Retrieve evidence for each pattern in the list of patterns and associate the results with each pattern.
        """
        results = []
        for pattern in patterns:
            sources = self.retrieve_for_pattern(pattern, top_k=top_k)
            results.append({
                "pattern_code": pattern.get("pattern_code"),
                "retrieved_sources": sources,
            })
        return results