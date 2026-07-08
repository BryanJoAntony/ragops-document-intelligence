from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.services.answer_generation_service import AnswerGenerationService
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
        score=0.87,
        text_preview="Audit history should be stored in PostgreSQL.",
        chunk_text="Audit history should be stored in PostgreSQL. Logs are useful for debugging.",
        metadata={
            "page_number": 1,
            "section_title": "Audit Requirements",
            "metadata_json": {"tags": ["audit"]},
        },
    )


def test_local_extractive_returns_no_context_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_ANSWER_PROVIDER", "local_extractive")
    service = AnswerGenerationService()

    result = service.generate_answer(
        question="What is the policy?",
        chunks=[],
    )

    assert "could not find enough indexed context" in result.answer
    assert result.citations == []
    assert result.provider == "local_extractive"


def test_local_extractive_uses_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_ANSWER_PROVIDER", "local_extractive")
    service = AnswerGenerationService()

    result = service.generate_answer(
        question="Where should audit history be stored?",
        chunks=[_sample_chunk()],
    )

    assert "[C1]" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].citation_id == "C1"
    assert result.model_name == "local_extractive_v1"
    assert result.provider == "local_extractive"
    assert result.total_token_estimate > 0


def test_explicit_answer_provider_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_ANSWER_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    service = AnswerGenerationService()

    result = service.generate_answer(
        question="Where should audit history be stored?",
        chunks=[_sample_chunk()],
        answer_provider="local_extractive",
    )

    assert result.provider == "local_extractive"


def test_openai_without_key_raises_clean_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    service = AnswerGenerationService()

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        service.generate_answer(
            question="Where should audit history be stored?",
            chunks=[_sample_chunk()],
            answer_provider="openai",
        )