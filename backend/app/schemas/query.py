from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class QueryAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class CitationResponse(BaseModel):
    citation_id: str
    document_id: UUID
    chunk_id: UUID
    chunk_index: int
    page_number: int | None
    section_title: str | None
    score: float
    text_preview: str


class QueryAnswerResponse(BaseModel):
    request_id: str
    question: str
    answer: str
    citations: list[CitationResponse]
    retrieval: dict[str, Any]
    model_name: str
    latency_ms: int


class QueryAuditResponse(BaseModel):
    request_id: str
    query_text: str
    retrieval_top_k: int
    retrieved_chunk_ids: list[str]
    answer_text: str | None
    model_name: str | None
    latency_ms: int | None
    token_estimate: int | None
    created_at: datetime