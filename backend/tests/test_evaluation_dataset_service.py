from app.schemas.evaluations import (
    EvaluationDatasetCreateRequest,
    EvaluationDatasetRunRequest,
    EvaluationQuestion,
)
from app.services.evaluation_dataset_service import EvaluationDatasetService


def test_evaluation_dataset_create_schema() -> None:
    request = EvaluationDatasetCreateRequest(
        name="core_storage_questions",
        description="Basic storage benchmark questions",
        questions=[
            EvaluationQuestion(
                question="Where should audit history be stored?",
                expected_answer="Audit history should be stored in PostgreSQL.",
                tags=["storage", "audit"],
            )
        ],
    )

    assert request.name == "core_storage_questions"
    assert len(request.questions) == 1
    assert request.questions[0].tags == ["storage", "audit"]


def test_evaluation_dataset_run_defaults() -> None:
    request = EvaluationDatasetRunRequest()

    assert request.retrieval_mode == "hybrid"
    assert request.top_k == 5
    assert request.answer_strategy == "single"


def test_extract_questions_from_dataset_json() -> None:
    class FakeDataset:
        dataset_json = {
            "questions": [
                {
                    "question": "What should Qdrant store?",
                    "expected_answer": "Qdrant should store vector embeddings.",
                    "document_id": None,
                    "tags": ["vector-db"],
                }
            ]
        }

    questions = EvaluationDatasetService.extract_questions(FakeDataset())

    assert len(questions) == 1
    assert questions[0]["question"] == "What should Qdrant store?"
    assert questions[0]["tags"] == ["vector-db"]


def test_extract_questions_rejects_invalid_format() -> None:
    class FakeDataset:
        dataset_json = {"questions": {"bad": "format"}}

    try:
        EvaluationDatasetService.extract_questions(FakeDataset())
    except ValueError as exc:
        assert "invalid questions format" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid questions format")
