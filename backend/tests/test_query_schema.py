import pytest
from pydantic import ValidationError

from app.schemas.query import QueryAskRequest


def test_query_ask_request_defaults() -> None:
    request = QueryAskRequest(question="Where is audit history stored?")

    assert request.retrieval_mode == "hybrid"
    assert request.answer_provider is None
    assert request.top_k == 5


def test_query_ask_request_accepts_openai_provider() -> None:
    request = QueryAskRequest(
        question="Where is audit history stored?",
        answer_provider="openai",
    )

    assert request.answer_provider == "openai"


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