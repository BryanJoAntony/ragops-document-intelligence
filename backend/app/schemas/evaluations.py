from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.query import AnswerProvider, AnswerStrategy, RetrievalMode


class EvaluationQuestion(BaseModel):
    question: str = Field(..., min_length=1)
    expected_answer: str | None = None
    document_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)


class EvaluationRunRequest(BaseModel):
    run_name: str = Field(..., min_length=1)
    questions: list[EvaluationQuestion] = Field(..., min_length=1)
    retrieval_mode: RetrievalMode = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    answer_strategy: AnswerStrategy = "single"
    answer_provider: AnswerProvider | None = None
    answer_providers: list[AnswerProvider] | None = None


class EvaluationDatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    questions: list[EvaluationQuestion] = Field(..., min_length=1)


class EvaluationDatasetRunRequest(BaseModel):
    run_name: str | None = None
    retrieval_mode: RetrievalMode = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    answer_strategy: AnswerStrategy = "single"
    answer_provider: AnswerProvider | None = None
    answer_providers: list[AnswerProvider] | None = None


class EvaluationDatasetResponse(BaseModel):
    dataset_id: UUID
    name: str
    description: str | None
    question_count: int
    dataset_json: dict[str, Any]
    created_at: Any


class EvaluationResultResponse(BaseModel):
    question: str
    expected_answer: str | None
    actual_answer: str
    request_id: str
    score: float
    retrieved_chunks_count: int
    citations_count: int
    evaluation_details: dict[str, Any]


class EvaluationRunResponse(BaseModel):
    run_id: UUID
    run_name: str
    retrieval_mode: str
    answer_strategy: str
    answer_provider: str | None
    answer_providers: list[str] | None
    total_questions: int
    average_score: float
    status: str
    created_at: Any
    results: list[EvaluationResultResponse]


class EvaluationRunSummaryResponse(BaseModel):
    run_id: str
    run_name: str
    run_source: str | None
    dataset_id: str | None
    dataset_name: str | None
    retrieval_mode: str
    answer_strategy: str
    answer_provider: str | None
    answer_providers: list[str] | None
    status: str
    total_questions: int
    result_count: int
    average_score: float
    computed_average_score: float | None
    average_citation_validation_score: float | None
    average_expected_answer_overlap: float | None
    average_latency_ms: float | None
    supported_claims_count: int
    unsupported_claims_count: int
    created_at: str | None


class EvaluationQuestionReportResponse(BaseModel):
    question: str
    expected_answer: str | None
    request_id: str
    score: float
    retrieved_chunks_count: int
    citations_count: int
    expected_answer_keyword_overlap: float | None
    citation_validation_score: float | None
    supported_claims_count: int | None
    unsupported_claims_count: int | None
    latency_ms: float | None
    answer_provider: str | None
    answer_strategy: str | None


class EvaluationRunReportResponse(BaseModel):
    run: EvaluationRunSummaryResponse
    per_question: list[EvaluationQuestionReportResponse]


class EvaluationRunComparisonDeltaResponse(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    candidate_run_name: str
    average_score_delta: float | None
    citation_validation_score_delta: float | None
    expected_overlap_delta: float | None
    latency_ms_delta: float | None


class EvaluationRunComparisonResponse(BaseModel):
    baseline_run_id: str
    run_count: int
    runs: list[EvaluationRunSummaryResponse]
    comparisons: list[EvaluationRunComparisonDeltaResponse]
