from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import DocumentChunk
from app.schemas.documents import (
    DocumentChunkResponse,
    DocumentIngestionResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    service = DocumentService(db)

    try:
        document, already_exists = await service.upload_document(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return DocumentUploadResponse(
        document=document,
        already_exists=already_exists,
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    service = DocumentService(db)
    return service.list_documents()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    service = DocumentService(db)
    document = service.get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return document


@router.post("/{document_id}/ingest", response_model=DocumentIngestionResponse)
def ingest_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentIngestionResponse:
    service = DocumentIngestionService(db)

    try:
        document, chunk_count = service.ingest_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DocumentIngestionResponse(
        document=document,
        chunk_count=chunk_count,
    )


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def list_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> list[DocumentChunkResponse]:
    service = DocumentService(db)
    document = service.get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )

    return list(db.scalars(statement).all())