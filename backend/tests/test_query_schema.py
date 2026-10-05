import pytest
from pydantic import ValidationError

from app.schemas.query import QueryAskRequest


def test_query_ask_request_defaults() -> None:
    request = QueryAskRequest(question="Where is audit history stored?")

    assert request.retrieval_mode == "hybrid"
    assert request.answer_strategy == "single"
    assert request.answer_provider is None
    assert request.answer_providers is None
    assert request.top_k == 5


def test_query_ask_request_accepts_openai_provider() -> None:
    request = QueryAskRequest(
        question="Where is audit history stored?",
        answer_provider="openai",
    )

    assert request.answer_provider == "openai"


def test_query_ask_request_accepts_local_summary_provider() -> None:
    request = QueryAskRequest(
        question="Where is audit history stored?",
        answer_provider="local_summary",
    )

    assert request.answer_provider == "local_summary"


def test_query_ask_request_accepts_compare_strategy() -> None:
    request = QueryAskRequest(
        question="Where is audit history stored?",
        answer_strategy="compare",
        answer_providers=["local_extractive", "local_summary"],
    )

    assert request.answer_strategy == "compare"
    assert request.answer_providers == ["local_extractive", "local_summary"]


def test_query_ask_request_deduplicates_compare_providers() -> None:
    request = QueryAskRequest(
        question="Where is audit history stored?",
        answer_strategy="compare",
        answer_providers=["local_extractive", "local_summary", "local_summary"],
    )

    assert request.answer_providers == ["local_extractive", "local_summary"]


def test_query_ask_request_rejects_invalid_retrieval_mode() -> None:
    with pytest.raises(ValidationError):
        QueryAskRequest(
            question="Where is audit history stored?",
            retrieval_mode="invalid_mode",
        )


def test_query_ask_request_rejects_invalid_answer_provider() -> None:
    with pytest.raises(ValidationError):
        QueryAskRequest(
            question="Where is audit history stored?",
            answer_provider="bad_provider",
        )


def test_query_ask_request_rejects_answer_providers_for_single_strategy() -> None:
    with pytest.raises(ValidationError):
        QueryAskRequest(
            question="Where is audit history stored?",
            answer_strategy="single",
            answer_providers=["local_extractive", "local_summary"],
        )


def test_query_ask_request_rejects_answer_provider_for_compare_strategy() -> None:
    with pytest.raises(ValidationError):
        QueryAskRequest(
            question="Where is audit history stored?",
            answer_strategy="compare",
            answer_provider="local_extractive",
            answer_providers=["local_extractive", "local_summary"],
        )


def test_query_ask_request_rejects_compare_without_providers() -> None:
    with pytest.raises(ValidationError):
        QueryAskRequest(
            question="Where is audit history stored?",
            answer_strategy="compare",
        )


def test_query_ask_request_rejects_compare_with_one_unique_provider() -> None:
    with pytest.raises(ValidationError):
        QueryAskRequest(
            question="Where is audit history stored?",
            answer_strategy="compare",
            answer_providers=["local_extractive", "local_extractive"],
        )
