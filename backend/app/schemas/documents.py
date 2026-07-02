from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    file_hash: str
    file_size_bytes: int
    status: str
    version: int
    error_message: str | None

    storage_backend: str | None
    storage_path: str | None
    storage_public_url: str | None

    generated_tags: list[str]
    detected_document_type: str | None
    language: str | None
    parser_name: str | None
    parsed_at: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    already_exists: bool


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    chunk_text: str
    page_number: int | None
    section_title: str | None
    token_estimate: int | None
    metadata_json: dict[str, Any]
    qdrant_point_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentIngestionResponse(BaseModel):
    document: DocumentResponse
    chunk_count: int


class DocumentIndexingResponse(BaseModel):
    document: DocumentResponse
    indexed_chunk_count: int


class RetrievedChunkResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    score: float
    text_preview: str
    chunk_text: str
    metadata: dict[str, Any]


class DocumentSearchRequest(BaseModel):
    query: str
    top_k: int = 5