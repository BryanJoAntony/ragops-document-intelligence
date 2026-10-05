from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


RetrievalMode = Literal["vector", "bm25", "fuzzy", "hybrid"]
AnswerProvider = Literal["local_extractive", "local_summary", "openai"]
AnswerStrategy = Literal["single", "compare"]


class RetrievalFilters(BaseModel):
    document_id: UUID | None = None
    workspace_id: UUID | None = None
    filename: str | None = None
    language: str | None = None
    parser_name: str | None = None
    document_type: str | None = None

    def has_filters(self) -> bool:
        return any(
            value is not None
            for value in self.model_dump().values()
        )


class QueryAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: UUID | None = None
    filters: RetrievalFilters | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: RetrievalMode = "hybrid"

    answer_strategy: AnswerStrategy = "single"
    answer_provider: AnswerProvider | None = None
    answer_providers: list[AnswerProvider] | None = None

    @model_validator(mode="after")
    def validate_request(self) -> "QueryAskRequest":
        if self.document_id is not None:
            if self.filters is None:
                self.filters = RetrievalFilters(document_id=self.document_id)
            elif self.filters.document_id is None:
                self.filters.document_id = self.document_id
            elif self.filters.document_id != self.document_id:
                raise ValueError("document_id and filters.document_id must match when both are provided.")

        if self.answer_strategy == "single":
            if self.answer_providers is not None:
                raise ValueError("answer_providers is only allowed when answer_strategy=compare.")
            return self

        if self.answer_strategy == "compare":
            if self.answer_provider is not None:
                raise ValueError("answer_provider is not allowed when answer_strategy=compare. Use answer_providers instead.")

            if not self.answer_providers:
                raise ValueError("answer_providers is required when answer_strategy=compare.")

            unique_providers = list(dict.fromkeys(self.answer_providers))
            if len(unique_providers) < 2:
                raise ValueError("answer_strategy=compare requires at least 2 unique providers.")

            self.answer_providers = unique_providers
            return self

        return self


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
    answer_strategy: str = "single"
    provider_count: int = 1
    input_token_estimate: int
    output_token_estimate: int
    total_token_estimate: int
    estimated_cost_usd: float


class ProviderOutputResponse(BaseModel):
    answer_provider: str
    model_name: str
    answer: str
    citations_used: int
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
    provider_outputs: list[ProviderOutputResponse] = []
    model_name: str
    latency_ms: int


class QueryAuditResponse(BaseModel):
    request_id: str
    query_text: str
    retrieval_top_k: int
    retrieval_mode: str | None
    query_filters: dict[str, Any] | None
    retrieved_chunk_ids: list[str]
    answer_text: str | None
    model_name: str | None
    latency_ms: int | None
    token_estimate: int | None
    created_at: datetime

