from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.services.answer_orchestration_service import AnswerOrchestrationService
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _sample_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        score=0.91,
        text_preview="RAG audit history should be stored in PostgreSQL.",
        chunk_text="RAG audit history should be stored in PostgreSQL. Qdrant should store vector embeddings.",
        metadata={
            "page_number": 1,
            "section_title": "RAGOps Storage",
            "metadata_json": {"tags": ["ragops", "audit"]},
        },
    )


def test_single_strategy_returns_one_provider_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_ANSWER_PROVIDER", "local_extractive")
    service = AnswerOrchestrationService()

    result = service.generate(
        question="Where should audit history be stored?",
        chunks=[_sample_chunk()],
        answer_strategy="single",
    )

    assert result.answer_strategy == "single"
    assert result.final_answer.provider == "local_extractive"
    assert len(result.provider_outputs) == 1


def test_single_strategy_accepts_explicit_provider() -> None:
    service = AnswerOrchestrationService()

    result = service.generate(
        question="Where should audit history be stored?",
        chunks=[_sample_chunk()],
        answer_strategy="single",
        answer_provider="local_summary",
    )

    assert result.answer_strategy == "single"
    assert result.final_answer.provider == "local_summary"
    assert len(result.provider_outputs) == 1


def test_compare_strategy_returns_multiple_provider_outputs() -> None:
    service = AnswerOrchestrationService()

    result = service.generate(
        question="Where should audit history be stored?",
        chunks=[_sample_chunk()],
        answer_strategy="compare",
        answer_providers=["local_extractive", "local_summary"],
    )

    assert result.answer_strategy == "compare"
    assert result.final_answer.provider == "local_extractive"
    assert [output.provider for output in result.provider_outputs] == [
        "local_extractive",
        "local_summary",
    ]


def test_compare_strategy_deduplicates_providers() -> None:
    service = AnswerOrchestrationService()

    result = service.generate(
        question="Where should audit history be stored?",
        chunks=[_sample_chunk()],
        answer_strategy="compare",
        answer_providers=["local_extractive", "local_summary", "local_summary"],
    )

    assert [output.provider for output in result.provider_outputs] == [
        "local_extractive",
        "local_summary",
    ]


def test_compare_strategy_requires_two_unique_providers() -> None:
    service = AnswerOrchestrationService()

    with pytest.raises(ValueError, match="at least 2 unique providers"):
        service.generate(
            question="Where should audit history be stored?",
            chunks=[_sample_chunk()],
            answer_strategy="compare",
            answer_providers=["local_extractive"],
        )
