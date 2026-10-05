from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.query import AnswerProvider, AnswerStrategy, RetrievalMode


RoutingTaskType = Literal["qa", "summary", "comparison", "evaluation"]
RoutingPriority = Literal["cost", "quality", "latency", "balanced"]


class ProviderCostEstimateResponse(BaseModel):
    provider: str
    input_token_estimate: int
    output_token_estimate: int
    total_token_estimate: int
    estimated_cost_usd: float
    within_budget: bool
    available: bool
    reason: str


class AnswerRoutingPlanRequest(BaseModel):
    question: str = Field(..., min_length=1)
    retrieval_mode: RetrievalMode = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    task_type: RoutingTaskType = "qa"
    priority: RoutingPriority = "balanced"
    allow_paid_providers: bool = False
    max_estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    require_compare: bool = False
    candidate_providers: list[AnswerProvider] = Field(
        default_factory=lambda: ["local_extractive", "local_summary", "openai"]
    )


class AnswerRoutingPlanResponse(BaseModel):
    recommended_answer_provider: str | None
    recommended_answer_strategy: AnswerStrategy
    recommended_answer_providers: list[str] | None
    priority: RoutingPriority
    task_type: RoutingTaskType
    estimated_context_tokens: int
    estimated_output_tokens: int
    provider_estimates: list[ProviderCostEstimateResponse]
    reasons: list[str]
    warnings: list[str]
