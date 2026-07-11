import hashlib
from typing import Iterable


class DeterministicFallbackEmbeddingModel:
    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def _encode_one(self, text: str):
        import numpy as np

        vector = np.zeros(self.dimensions, dtype=float)
        tokens = text.lower().split()

        for token in tokens or [text.lower()]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = np.linalg.norm(vector)
        if norm:
            vector = vector / norm

        return vector

    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True):
        import numpy as np

        if isinstance(texts, str):
            return self._encode_one(texts)

        return np.array([self._encode_one(text) for text in texts], dtype=float)


class EmbeddingService:
    """
    Service responsible for converting text into vector embeddings.

    It first tries to load the preferred biomedical embedding model:
    NeuML/pubmedbert-base-embeddings

    If that fails, it falls back to:
    sentence-transformers/all-MiniLM-L6-v2
    """

    def __init__(
        self,
        preferred_model_name: str = "NeuML/pubmedbert-base-embeddings",
        fallback_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.preferred_model_name = preferred_model_name
        self.fallback_model_name = fallback_model_name
        self.model_name: str | None = None
        self.model = None

    def _load_model(self):
        """
        Load the embedding model lazily.

        Lazy loading means the model is not loaded when the service object is created.
        It is loaded only when embed_text() or embed_texts() is called.
        """

        if self.model is not None:
            return self.model

        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.preferred_model_name, local_files_only=True)
            self.model_name = self.preferred_model_name
            return self.model

        except Exception as preferred_error:
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(self.fallback_model_name, local_files_only=True)
                self.model_name = self.fallback_model_name
                return self.model

            except Exception as fallback_error:
                self.model = DeterministicFallbackEmbeddingModel()
                self.model_name = "deterministic-local-fallback"
                return self.model

    def _validate_text(self, text: str) -> str:
        """
        Validate and clean a single text input.
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string.")

        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError("text cannot be empty.")

        return cleaned_text

    def embed_text(self, text: str) -> list[float]:
        """
        Convert one text string into one embedding vector.

        Example:
        embed_text("High troponin with chest pain")
        -> [0.012, -0.44, 0.21, ...]
        """

        cleaned_text = self._validate_text(text)
        model = self._load_model()

        embedding = model.encode(
            cleaned_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.astype(float).tolist()

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        """
        Convert multiple text strings into multiple embedding vectors.

        This will be useful for the Knowledge Indexer in T15.
        """

        if isinstance(texts, str):
            raise TypeError("texts must be an iterable of strings, not a single string.")

        cleaned_texts = [self._validate_text(text) for text in texts]

        if not cleaned_texts:
            raise ValueError("texts cannot be empty.")

        model = self._load_model()

        embeddings = model.encode(
            cleaned_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.astype(float).tolist()

    def get_model_info(self) -> dict[str, str | None]:
        """
        Return information about the loaded model.

        If no embedding has been generated yet, model_name will still be None
        because loading is lazy.
        """

        return {
            "preferred_model_name": self.preferred_model_name,
            "fallback_model_name": self.fallback_model_name,
            "active_model_name": self.model_name,
        }
