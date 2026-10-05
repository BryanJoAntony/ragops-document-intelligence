from app.schemas.routing import AnswerRoutingPlanRequest
from app.services.model_routing_service import ModelRoutingService


def test_estimate_context_tokens_uses_top_k() -> None:
    tokens = ModelRoutingService.estimate_context_tokens(
        question="Where should audit history be stored?",
        top_k=5,
    )

    assert tokens > 900


def test_estimate_output_tokens_varies_by_task_type() -> None:
    summary_tokens = ModelRoutingService.estimate_output_tokens(
        task_type="summary",
        question="Summarize this document.",
    )
    qa_tokens = ModelRoutingService.estimate_output_tokens(
        task_type="qa",
        question="Where should audit history be stored?",
    )

    assert summary_tokens > qa_tokens


def test_local_provider_cost_is_zero() -> None:
    service = ModelRoutingService()

    estimate = service.estimate_provider_cost(
        provider="local_extractive",
        input_token_estimate=1000,
        output_token_estimate=100,
        allow_paid_providers=False,
        max_estimated_cost_usd=0.0,
        openai_configured=False,
    )

    assert estimate["estimated_cost_usd"] == 0.0
    assert estimate["within_budget"] is True
    assert estimate["available"] is True


def test_openai_is_unavailable_without_config() -> None:
    service = ModelRoutingService()

    estimate = service.estimate_provider_cost(
        provider="openai",
        input_token_estimate=1000,
        output_token_estimate=100,
        allow_paid_providers=True,
        max_estimated_cost_usd=1.0,
        openai_configured=False,
    )

    assert estimate["available"] is False
    assert estimate["within_budget"] is False


def test_routing_defaults_to_local_extractive() -> None:
    service = ModelRoutingService()
    request = AnswerRoutingPlanRequest(
        question="Where should audit history be stored?",
    )

    plan = service.build_answer_plan(
        request=request,
        openai_configured=False,
    )

    assert plan["recommended_answer_provider"] == "local_extractive"
    assert plan["recommended_answer_strategy"] == "single"


def test_summary_task_prefers_local_summary() -> None:
    service = ModelRoutingService()
    request = AnswerRoutingPlanRequest(
        question="Summarize this policy.",
        task_type="summary",
    )

    plan = service.build_answer_plan(
        request=request,
        openai_configured=False,
    )

    assert plan["recommended_answer_provider"] == "local_summary"


def test_compare_requires_two_available_providers() -> None:
    service = ModelRoutingService()
    request = AnswerRoutingPlanRequest(
        question="Compare these answer providers.",
        require_compare=True,
        candidate_providers=["local_extractive", "local_summary"],
    )

    plan = service.build_answer_plan(
        request=request,
        openai_configured=False,
    )

    assert plan["recommended_answer_strategy"] == "compare"
    assert plan["recommended_answer_providers"] == ["local_extractive", "local_summary"]


def test_quality_priority_can_select_openai_when_allowed_and_configured() -> None:
    service = ModelRoutingService()
    request = AnswerRoutingPlanRequest(
        question="Explain this complex document policy.",
        priority="quality",
        allow_paid_providers=True,
        max_estimated_cost_usd=1.0,
        candidate_providers=["local_extractive", "openai"],
    )

    plan = service.build_answer_plan(
        request=request,
        openai_configured=True,
    )

    assert plan["recommended_answer_provider"] == "openai"
