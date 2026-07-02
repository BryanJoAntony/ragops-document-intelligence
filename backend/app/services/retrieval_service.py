from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.utils.text import text_preview


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    score: float
    text_preview: str
    chunk_text: str
    metadata: dict


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

    def vector_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        query_vector = self.embedding_service.embed_query(query)
        hits = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            document_id=document_id,
        )

        results: list[RetrievedChunk] = []

        for hit in hits:
            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id")

            if not chunk_id:
                continue

            chunk = self.db.get(DocumentChunk, UUID(chunk_id))
            if chunk is None:
                continue

            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    score=float(hit.score),
                    text_preview=text_preview(chunk.chunk_text),
                    chunk_text=chunk.chunk_text,
                    metadata={
                        "qdrant_point_id": str(hit.id),
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "metadata_json": chunk.metadata_json,
                    },
                )
            )

        return results