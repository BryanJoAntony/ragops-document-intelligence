from uuid import uuid4

from app.services.answer_generation_service import AnswerGenerationService
from app.services.retrieval_service import RetrievedChunk


def test_answer_generation_returns_no_context_message() -> None:
    service = AnswerGenerationService()

    result = service.generate_answer(
        question="What is the policy?",
        chunks=[],
    )

    assert "could not find enough indexed context" in result.answer
    assert result.citations == []


def test_answer_generation_uses_citations() -> None:
    service = AnswerGenerationService()

    chunk = RetrievedChunk(
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

    result = service.generate_answer(
        question="Where should audit history be stored?",
        chunks=[chunk],
    )

    assert "[C1]" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].citation_id == "C1"
    assert result.model_name == "local_extractive_v1"