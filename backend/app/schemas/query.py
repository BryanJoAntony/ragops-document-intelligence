from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


RetrievalMode = Literal["vector", "bm25", "fuzzy", "hybrid"]
AnswerProvider = Literal["local_extractive", "openai"]


class QueryAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: RetrievalMode = "hybrid"
    answer_provider: AnswerProvider | None = None


class CitationResponse(BaseModel):
    citation_id: str
    document_id: UUID
    chunk_id: UUID
    chunk_index: int
    page_number: int | None
    section_title: str | None
    score: float
    text_preview: str


class AnswerMetadataResponse(BaseModel):
    answer_provider: str
    input_token_estimate: int
    output_token_estimate: int
    total_token_estimate: int
    estimated_cost_usd: float


class QueryAnswerResponse(BaseModel):
    request_id: str
    question: str
    answer: str
    citations: list[CitationResponse]
    retrieval: dict[str, Any]
    answer_metadata: AnswerMetadataResponse
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