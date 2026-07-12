import hashlib
import os
from typing import Iterable


DEFAULT_EMBEDDING_MODEL_NAME = "NeuML/pubmedbert-base-embeddings"
DEFAULT_EMBEDDING_VECTOR_DIMENSION = 768


class DeterministicFallbackEmbeddingModel:
    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_VECTOR_DIMENSION):
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

    The model is configured with EMBEDDING_MODEL_NAME and defaults to the
    canonical biomedical model used by indexing, retrieval, and evaluation.
    """

    def __init__(
        self,
        model_name: str | None = None,
        local_files_only: bool | None = None,
        expected_dimension: int | None = None,
    ):
        self.configured_model_name = model_name or os.getenv(
            "EMBEDDING_MODEL_NAME",
            DEFAULT_EMBEDDING_MODEL_NAME,
        )
        self.local_files_only = (
            self._read_bool("EMBEDDING_LOCAL_FILES_ONLY", default=True)
            if local_files_only is None
            else local_files_only
        )
        self.expected_dimension = expected_dimension or int(
            os.getenv("EMBEDDING_VECTOR_DIMENSION", str(DEFAULT_EMBEDDING_VECTOR_DIMENSION))
        )
        self.active_model_name: str | None = None
        self.vector_dimension: int | None = None
        self.model = None

    def _read_bool(self, name: str, default: bool = False) -> bool:
        if os.getenv("HF_HUB_OFFLINE") == "1" or os.getenv("TRANSFORMERS_OFFLINE") == "1":
            return True
        raw_value = os.getenv(name)
        if raw_value is None:
            return default
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}

    def _model_dimension(self, model) -> int | None:
        for attribute in ("get_embedding_dimension", "get_sentence_embedding_dimension"):
            method = getattr(model, attribute, None)
            if callable(method):
                dimension = method()
                if dimension is not None:
                    return int(dimension)
        return getattr(model, "dimensions", None)

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

            self.model = SentenceTransformer(
                self.configured_model_name,
                local_files_only=self.local_files_only,
            )
            self.active_model_name = self.configured_model_name
        except Exception as error:
            raise RuntimeError(
                "Embedding model could not be loaded. "
                f"Configured EMBEDDING_MODEL_NAME={self.configured_model_name!r}; "
                f"local_files_only={self.local_files_only}. "
                "Install/cache the canonical model or allow model download, then reindex "
                "the Qdrant medical_knowledge collection."
            ) from error

        self.vector_dimension = self._model_dimension(self.model)
        if self.vector_dimension != self.expected_dimension:
            raise RuntimeError(
                "Embedding model dimension mismatch. "
                f"{self.configured_model_name!r} produced {self.vector_dimension}; "
                f"expected {self.expected_dimension}. Update EMBEDDING_VECTOR_DIMENSION "
                "or reconfigure EMBEDDING_MODEL_NAME consistently."
            )

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

    def get_vector_dimension(self) -> int:
        self._load_model()
        if self.vector_dimension is None:
            raise RuntimeError("Active embedding model did not expose a vector dimension.")
        return self.vector_dimension

    def get_model_info(self) -> dict[str, str | int | bool | None]:
        """
        Return information about the loaded model.

        If no embedding has been generated yet, model_name will still be None
        because loading is lazy.
        """

        return {
            "configured_model_name": self.configured_model_name,
            "active_model_name": self.active_model_name,
            "vector_dimension": self.vector_dimension,
            "expected_dimension": self.expected_dimension,
            "local_files_only": self.local_files_only,
        }
