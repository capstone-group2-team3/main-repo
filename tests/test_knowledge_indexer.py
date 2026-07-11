from pathlib import Path

from app.services.knowledge_indexer import KnowledgeIndexer


class FakeEmbeddingService:
    def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def get_model_info(self):
        return {
            "preferred_model_name": "fake",
            "fallback_model_name": "fake",
            "active_model_name": "fake-test-model",
        }


def test_chunk_markdown_text_splits_by_headings(tmp_path):
    indexer = KnowledgeIndexer(
        knowledge_dir=str(tmp_path),
        embedding_service=FakeEmbeddingService(),
    )

    text = """
# CBC Interpretation

Hemoglobin is used to support anemia-related pattern review.

## High Values

High values may require clinician review.

## Low Values

Low hemoglobin may support anemia-related pattern review.
"""

    chunks = indexer._chunk_markdown_text(text)

    assert len(chunks) >= 2
    assert any("CBC Interpretation" in chunk for chunk in chunks)


def test_build_chunks_from_file(tmp_path):
    file_path = tmp_path / "cbc_interpretation.md"
    file_path.write_text(
        "# CBC Interpretation\n\nLow hemoglobin may support anemia-related pattern review.",
        encoding="utf-8",
    )

    indexer = KnowledgeIndexer(
        knowledge_dir=str(tmp_path),
        embedding_service=FakeEmbeddingService(),
    )

    metadata, chunks = indexer._build_chunks_from_file(file_path)

    assert metadata["source_id"] == "cbc_interpretation"
    assert metadata["title"] == "CBC Interpretation"
    assert metadata["panel"] == "CBC Panel"
    assert metadata["canonical_panel"] == "CBC_Panel"
    assert metadata["file_name"] == "cbc_interpretation.md"
    assert metadata["source_type"] == "internal_medical_knowledge"
    assert metadata["chunk_count"] == len(chunks)
    assert len(chunks) >= 1
    assert chunks[0]["source_id"] == "cbc_interpretation"
    assert chunks[0]["section_title"] == "CBC Interpretation"
    assert chunks[0]["canonical_panel"] == "CBC_Panel"
    assert "Hemoglobin" in chunks[0]["related_tests"]
    assert "anemia_pattern" in chunks[0]["pattern_codes"]
    assert "hemoglobin" in chunks[0]["normalized_terms"]


def test_get_markdown_files_only_returns_md_files(tmp_path):
    (tmp_path / "a.md").write_text("# A", encoding="utf-8")
    (tmp_path / "b.txt").write_text("B", encoding="utf-8")

    indexer = KnowledgeIndexer(
        knowledge_dir=str(tmp_path),
        embedding_service=FakeEmbeddingService(),
    )

    files = indexer._get_markdown_files()

    assert len(files) == 1
    assert files[0].name == "a.md"


def test_infer_panel_from_filename():
    indexer = KnowledgeIndexer(embedding_service=FakeEmbeddingService())

    assert indexer._infer_panel_from_filename("cbc_interpretation.md") == "CBC Panel"
    assert indexer._infer_panel_from_filename("diabetic_rapid_glucose.md") == "Diabetic / Rapid Glucose Panel"
    assert indexer._infer_panel_from_filename("renal_thyroid.md") == "Renal & Thyroid Panel"
    assert indexer._infer_panel_from_filename("safety_guidelines.md") == "Safety Guidelines"
    assert indexer._infer_canonical_panel("cardiac_enzymes.md") == "Cardiac_Enzymes_Panel"
