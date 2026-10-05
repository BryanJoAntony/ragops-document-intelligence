from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.query import AnswerProvider, AnswerStrategy, RetrievalMode


class CitationValidationRunRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: RetrievalMode = "hybrid"
    answer_strategy: AnswerStrategy = "single"
    answer_provider: AnswerProvider | None = None
    answer_providers: list[AnswerProvider] | None = None


class ValidatedCitationResponse(BaseModel):
    citation_id: str
    citation_marker: str
    chunk_id: UUID | None
    document_id: UUID | None
    marker_found_in_answer: bool
    citation_provided: bool


class ClaimValidationResponse(BaseModel):
    claim_text: str
    citation_marker: str | None
    citation_id: str | None
    supported: bool
    support_score: float
    reason: str


class CitationValidationResponse(BaseModel):
    validation_id: UUID
    request_id: str
    question: str
    answer: str
    validation_score: float
    citation_markers_found: list[str]
    citations_provided_count: int
    cited_claims_count: int
    supported_claims_count: int
    unsupported_claims_count: int
    validated_citations: list[ValidatedCitationResponse]
    claim_validations: list[ClaimValidationResponse]
    validation_details: dict[str, Any]
