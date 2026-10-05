import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.services.chunking import ChunkingService
from app.services.document_parser import DocumentParserService
from app.services.metadata_tagger import MetadataTaggingService
from app.services.storage import get_storage_service

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_service()
        self.parser = DocumentParserService()
        self.chunker = ChunkingService()
        self.tagger = MetadataTaggingService()

    def ingest_document(self, document_id: UUID) -> tuple[Document, int]:
        document = self.db.get(Document, document_id)

        if document is None:
            raise ValueError("Document not found.")

        if not document.storage_path:
            raise ValueError("Document has no storage path.")

        try:
            file_bytes = self.storage.get_file(document.storage_path)
            parsed_document = self.parser.parse(
                filename=document.filename,
                content_type=document.content_type,
                file_bytes=file_bytes,
            )

            if not parsed_document.full_text:
                raise ValueError("No text could be extracted from the document.")

            chunks = self.chunker.chunk_document(parsed_document)

            if not chunks:
                raise ValueError("Document parsing succeeded, but no chunks were generated.")

            document.generated_tags = self.tagger.generate_document_tags(
                filename=document.filename,
                text=parsed_document.full_text,
            )
            document.detected_document_type = self.tagger.detect_document_type(
                filename=document.filename,
                text=parsed_document.full_text,
            )
            document.language = self.tagger.detect_language(parsed_document.full_text)
            document.parser_name = parsed_document.parser_name
            document.status = "parsed"
            document.error_message = None
            document.parsed_at = datetime.now(UTC)

            # Re-ingestion should replace old chunks to keep chunk metadata consistent with the latest parser logic.
            self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))

            for chunk in chunks:
                chunk_tags = self.tagger.generate_chunk_tags(
                    text=chunk.chunk_text,
                    section_title=chunk.section_title,
                )

                metadata = dict(chunk.metadata)
                metadata["tags"] = chunk_tags
                metadata["contains_table"] = False
                metadata["contains_ocr_text"] = False

                self.db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        chunk_text=chunk.chunk_text,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        token_estimate=chunk.token_estimate,
                        metadata_json=metadata,
                    )
                )

            self.db.commit()
            self.db.refresh(document)

            logger.info(
                "Document ingested",
                extra={
                    "document_id": str(document.id),
                    "chunk_count": len(chunks),
                    "parser_name": parsed_document.parser_name,
                    "detected_document_type": document.detected_document_type,
                },
            )

            return document, len(chunks)

        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)
            self.db.commit()

            logger.exception(
                "Document ingestion failed",
                extra={"document_id": str(document.id)},
            )

            raise