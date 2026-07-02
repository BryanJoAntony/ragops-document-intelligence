import logging
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class DocumentIndexingService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

    def index_document(self, document_id: UUID) -> tuple[Document, int]:
        document = self.db.get(Document, document_id)

        if document is None:
            raise ValueError("Document not found.")

        if document.status not in {"parsed", "indexed"}:
            raise ValueError("Document must be parsed before indexing.")

        chunks = self._get_chunks(document_id)

        if not chunks:
            raise ValueError("Document has no chunks to index.")

        texts = [chunk.chunk_text for chunk in chunks]
        embeddings = self.embedding_service.embed_texts(texts)

        points: list[tuple[str, list[float], dict]] = []

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            point_id = chunk.qdrant_point_id or str(uuid.uuid4())
            chunk.qdrant_point_id = point_id

            payload = {
                "document_id": str(document.id),
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "filename": document.filename,
                "document_type": document.detected_document_type,
                "document_tags": document.generated_tags,
                "chunk_tags": chunk.metadata_json.get("tags", []),
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
            }

            points.append((point_id, embedding, payload))

        self.vector_store.upsert_chunk_vectors(points)

        document.status = "indexed"
        self.db.commit()
        self.db.refresh(document)

        logger.info(
            "Document indexed",
            extra={
                "document_id": str(document.id),
                "chunk_count": len(chunks),
                "collection_name": self.vector_store.collection_name,
            },
        )

        return document, len(chunks)

    def _get_chunks(self, document_id: UUID) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(statement).all())