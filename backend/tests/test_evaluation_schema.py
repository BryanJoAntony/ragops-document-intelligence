from app.schemas.evaluations import EvaluationRunRequest


def test_evaluation_run_request_defaults() -> None:
    request = EvaluationRunRequest(
        run_name="basic_eval",
        questions=[
            {
                "question": "Where should audit history be stored?",
                "expected_answer": "Audit history should be stored in PostgreSQL.",
            }
        ],
    )

    assert request.run_name == "basic_eval"
    assert request.retrieval_mode == "hybrid"
    assert request.top_k == 5
    assert request.answer_strategy == "single"
    assert request.answer_provider is None
    assert request.answer_providers is None
    assert len(request.questions) == 1


def test_evaluation_run_request_accepts_compare_strategy() -> None:
    request = EvaluationRunRequest(
        run_name="compare_eval",
        questions=[
            {
                "question": "Where should audit history be stored?",
            }
        ],
        answer_strategy="compare",
        answer_providers=["local_extractive", "local_summary"],
    )

    assert request.answer_strategy == "compare"
    assert request.answer_providers == ["local_extractive", "local_summary"]
