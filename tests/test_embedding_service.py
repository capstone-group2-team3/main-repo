import pytest

from app.services.embedding_service import EmbeddingService


class FakeModel:
    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True):
        import numpy as np

        if isinstance(texts, str):
            return np.array([0.1, 0.2, 0.3])

        return np.array([
            [0.1, 0.2, 0.3]
            for _ in texts
        ])


class FakeEmbeddingService(EmbeddingService):
    def _load_model(self):
        self.model = FakeModel()
        self.active_model_name = "fake-test-model"
        self.vector_dimension = 3
        return self.model


def test_embed_text_returns_list_of_floats():
    service = FakeEmbeddingService()

    vector = service.embed_text("High troponin with chest pain")

    assert isinstance(vector, list)
    assert len(vector) == 3
    assert all(isinstance(value, float) for value in vector)


def test_embed_texts_returns_list_of_vectors():
    service = FakeEmbeddingService()

    vectors = service.embed_texts([
        "High glucose",
        "Low hemoglobin",
    ])

    assert isinstance(vectors, list)
    assert len(vectors) == 2
    assert all(isinstance(vector, list) for vector in vectors)
    assert all(len(vector) == 3 for vector in vectors)


def test_embed_text_rejects_empty_text():
    service = FakeEmbeddingService()

    with pytest.raises(ValueError):
        service.embed_text("   ")


def test_embed_text_rejects_non_string():
    service = FakeEmbeddingService()

    with pytest.raises(TypeError):
        service.embed_text(123)


def test_embed_texts_rejects_single_string():
    service = FakeEmbeddingService()

    with pytest.raises(TypeError):
        service.embed_texts("this should be a list, not a string")


def test_model_info_before_loading():
    service = EmbeddingService()

    info = service.get_model_info()

    assert info["configured_model_name"] == "NeuML/pubmedbert-base-embeddings"
    assert info["active_model_name"] is None
    assert info["expected_dimension"] == 768
