import os
import re
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.repositories import save_knowledge_doc_metadata
from app.services.embedding_service import EmbeddingService


class KnowledgeIndexer:
    """
    Reads curated medical knowledge markdown files, chunks them,
    creates embeddings, stores vectors in Qdrant, and stores file metadata in SQL.
    """

    def __init__(
        self,
        knowledge_dir: str | None = None,
        collection_name: str = "medical_knowledge",
        qdrant_url: str | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        project_root = Path(__file__).resolve().parents[2]

        self.project_root = project_root
        self.knowledge_dir = (
            Path(knowledge_dir)
            if knowledge_dir
            else project_root / "medical_knowledge"
        )

        self.collection_name = collection_name
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.embedding_service = embedding_service or EmbeddingService()
        self.client = None

    def _get_qdrant_client(self):
        """
        Lazily create Qdrant client.

        Lazy loading prevents app startup from failing if Qdrant is not needed yet.
        """

        if self.client is not None:
            return self.client

        from qdrant_client import QdrantClient

        self.client = QdrantClient(url=self.qdrant_url)
        return self.client

    def _get_markdown_files(self) -> list[Path]:
        """
        Return direct markdown files from medical_knowledge/.
        """

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {self.knowledge_dir}")

        return sorted(self.knowledge_dir.glob("*.md"))

    def _title_from_markdown(self, path: Path, text: str) -> str:
        """
        Extract title from the first markdown heading.
        If no heading exists, use the filename.
        """

        for line in text.splitlines():
            clean_line = line.strip()
            if clean_line.startswith("#"):
                title = clean_line.lstrip("#").strip()
                if title:
                    return title

        return path.stem.replace("_", " ").title()

    def _infer_panel_from_filename(self, filename: str) -> str | None:
        """
        Infer panel name from the markdown filename.
        """

        name = filename.lower()

        if "cbc" in name or "anemia" in name:
            return "CBC Panel"

        if "diabetic" in name or "glucose" in name:
            return "Diabetic / Rapid Glucose Panel"

        if "renal" in name or "thyroid" in name:
            return "Renal & Thyroid Panel"

        if "lipids" in name or "inflammation" in name:
            return "Lipids & Inflammation Panel"

        if "cardiac" in name or "troponin" in name or "cpk" in name:
            return "Cardiac Enzymes Panel"

        if "electrolytes" in name or "calcium" in name:
            return "Electrolytes & Calcium Panel"

        if "albumin" in name or "protein" in name:
            return "Protein / Albumin Panel"

        if "safety" in name:
            return "Safety Guidelines"

        return None

    def _split_by_headings(self, text: str) -> list[str]:
        """
        Split markdown text by headings.
        """

        sections: list[str] = []
        current_section: list[str] = []

        for line in text.splitlines():
            is_heading = bool(re.match(r"^#{1,3}\s+", line.strip()))

            if is_heading and current_section:
                section_text = "\n".join(current_section).strip()
                if section_text:
                    sections.append(section_text)
                current_section = [line]
            else:
                current_section.append(line)

        if current_section:
            section_text = "\n".join(current_section).strip()
            if section_text:
                sections.append(section_text)

        if not sections and text.strip():
            sections.append(text.strip())

        return sections

    def _split_long_text(
        self,
        text: str,
        max_words: int = 250,
        overlap_words: int = 40,
    ) -> list[str]:
        """
        Split long sections into smaller chunks with word overlap.
        """

        words = text.split()

        if len(words) <= max_words:
            return [text.strip()]

        chunks = []
        start = 0
        step = max_words - overlap_words

        while start < len(words):
            end = start + max_words
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words).strip()

            if chunk_text:
                chunks.append(chunk_text)

            start += step

        return chunks

    def _chunk_markdown_text(self, text: str) -> list[str]:
        """
        Chunk markdown text by headings, then split long sections.
        """

        sections = self._split_by_headings(text)

        chunks: list[str] = []

        for section in sections:
            section_chunks = self._split_long_text(section)
            chunks.extend(section_chunks)

        return [chunk for chunk in chunks if chunk.strip()]

    def _relative_file_path(self, path: Path) -> str:
        """
        Return a stable relative path if possible.
        """

        try:
            return str(path.relative_to(self.project_root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _build_chunks_from_file(self, path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """
        Read one markdown file and return file metadata + chunk records.
        """

        text = path.read_text(encoding="utf-8")
        title = self._title_from_markdown(path, text)
        chunks = self._chunk_markdown_text(text)

        source_id = path.stem
        panel = self._infer_panel_from_filename(path.name)
        relative_path = self._relative_file_path(path)

        metadata = {
            "source_id": source_id,
            "title": title,
            "file_path": relative_path,
            "panel": panel,
            "chunk_count": len(chunks),
        }

        chunk_records = []

        for index, chunk_text in enumerate(chunks):
            chunk_records.append(
                {
                    "source_id": source_id,
                    "title": title,
                    "file_path": relative_path,
                    "panel": panel,
                    "chunk_index": index,
                    "chunk_text": chunk_text,
                }
            )

        return metadata, chunk_records

    def _reset_collection(self, vector_size: int) -> None:
        """
        Delete and recreate the Qdrant collection.

        This keeps indexing idempotent for the MVP.
        """

        from qdrant_client.http import models

        client = self._get_qdrant_client()

        if client.collection_exists(self.collection_name):
            client.delete_collection(self.collection_name)

        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def _upsert_chunks_to_qdrant(
        self,
        chunk_records: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> None:
        """
        Store chunk vectors and metadata payloads in Qdrant.
        """

        from qdrant_client.http import models

        client = self._get_qdrant_client()

        points = []

        for chunk, vector in zip(chunk_records, vectors):
            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{chunk['source_id']}-{chunk['chunk_index']}",
                )
            )

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "source_id": chunk["source_id"],
                        "title": chunk["title"],
                        "file_path": chunk["file_path"],
                        "panel": chunk["panel"],
                        "chunk_index": chunk["chunk_index"],
                        "chunk_text": chunk["chunk_text"],
                    },
                )
            )

        client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def index_medical_knowledge(self, db: Session | None = None) -> dict[str, Any]:
        """
        Main entry point for T15.

        Reads medical_knowledge/*.md, chunks them, embeds the chunks,
        stores them in Qdrant, and optionally stores file metadata in SQL.
        """

        markdown_files = self._get_markdown_files()

        if not markdown_files:
            raise ValueError("No markdown files found in medical_knowledge/.")

        all_file_metadata: list[dict[str, Any]] = []
        all_chunk_records: list[dict[str, Any]] = []

        for path in markdown_files:
            file_metadata, chunk_records = self._build_chunks_from_file(path)

            if chunk_records:
                all_file_metadata.append(file_metadata)
                all_chunk_records.extend(chunk_records)

        if not all_chunk_records:
            raise ValueError("No chunks were generated from the knowledge files.")

        chunk_texts = [chunk["chunk_text"] for chunk in all_chunk_records]
        vectors = self.embedding_service.embed_texts(chunk_texts)

        if not vectors:
            raise ValueError("No embeddings were generated.")

        vector_size = len(vectors[0])

        self._reset_collection(vector_size)
        self._upsert_chunks_to_qdrant(all_chunk_records, vectors)

        if db is not None:
            for metadata in all_file_metadata:
                save_knowledge_doc_metadata(db, metadata)

        return {
            "status": "ok",
            "collection_name": self.collection_name,
            "qdrant_url": self.qdrant_url,
            "files_indexed": len(all_file_metadata),
            "chunks_indexed": len(all_chunk_records),
            "vector_size": vector_size,
            "indexed_files": all_file_metadata,
            "embedding_model": self.embedding_service.get_model_info(),
        }