import logging
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document
from app.services.storage import get_storage_service
from app.utils.hashing import build_stored_filename, sha256_bytes

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_service()

    async def upload_document(self, file: UploadFile) -> tuple[Document, bool]:
        content = await file.read()

        if not content:
            raise ValueError("Uploaded file is empty.")

        file_hash = sha256_bytes(content)
        existing_document = self._get_document_by_hash(file_hash)
        stored_filename = build_stored_filename(file_hash, file.filename or "uploaded_file")

        if existing_document:
            stored_file = self.storage.ensure_file_exists(content, stored_filename)

            if not existing_document.storage_path:
                existing_document.storage_backend = stored_file.storage_backend
                existing_document.storage_path = stored_file.storage_path
                existing_document.storage_public_url = stored_file.public_url
                self.db.commit()
                self.db.refresh(existing_document)

            return existing_document, True

        stored_file = self.storage.save_file(content, stored_filename)

        document = Document(
            filename=file.filename or "uploaded_file",
            content_type=file.content_type or "application/octet-stream",
            file_hash=file_hash,
            file_size_bytes=len(content),
            status="uploaded",
            version=1,
            storage_backend=stored_file.storage_backend,
            storage_path=stored_file.storage_path,
            storage_public_url=stored_file.public_url,
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        logger.info(
            "Document uploaded",
            extra={
                "document_id": str(document.id),
                "file_hash": file_hash,
                "file_size_bytes": len(content),
                "storage_backend": stored_file.storage_backend,
            },
        )

        return document, False

    def list_documents(self) -> list[Document]:
        statement = select(Document).order_by(Document.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_document(self, document_id: UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def _get_document_by_hash(self, file_hash: str) -> Document | None:
        statement = select(Document).where(Document.file_hash == file_hash)
        return self.db.scalars(statement).first()