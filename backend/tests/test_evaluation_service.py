from app.services.evaluation_service import EvaluationService


def test_important_terms_removes_stopwords() -> None:
    terms = EvaluationService._important_terms(
        "Audit history should be stored in PostgreSQL."
    )

    assert "audit" in terms
    assert "history" in terms
    assert "postgresql" in terms
    assert "should" not in terms


def test_score_answer_without_expected_answer() -> None:
    service = EvaluationService.__new__(EvaluationService)

    score, details = service._score_answer(
        actual_answer="Audit history is stored in PostgreSQL. [C1]",
        expected_answer=None,
        citations_count=1,
        retrieved_chunks_count=1,
        citation_validation_score=1.0,
    )

    assert score == 1.0
    assert details["score_parts"]["has_answer"] == 1.0
    assert details["score_parts"]["has_citations"] == 1.0
    assert details["score_parts"]["has_retrieved_context"] == 1.0
    assert details["score_parts"]["citation_validation_score"] == 1.0


def test_score_answer_with_expected_answer_overlap_and_citation_validation() -> None:
    service = EvaluationService.__new__(EvaluationService)

    score, details = service._score_answer(
        actual_answer="Audit history is stored in PostgreSQL. [C1]",
        expected_answer="Audit history should be stored in PostgreSQL.",
        citations_count=1,
        retrieved_chunks_count=1,
        citation_validation_score=1.0,
    )

    assert score > 0.8
    assert details["score_parts"]["expected_answer_keyword_overlap"] > 0.0
    assert details["score_parts"]["citation_validation_score"] == 1.0


def test_score_answer_penalizes_missing_citations() -> None:
    service = EvaluationService.__new__(EvaluationService)

    score, details = service._score_answer(
        actual_answer="Audit history is stored in PostgreSQL.",
        expected_answer="Audit history should be stored in PostgreSQL.",
        citations_count=0,
        retrieved_chunks_count=1,
        citation_validation_score=0.0,
    )

    assert score < 1.0
    assert details["score_parts"]["has_citations"] == 0.0
    assert details["score_parts"]["citation_validation_score"] == 0.0


def test_score_answer_uses_citation_validation_score() -> None:
    service = EvaluationService.__new__(EvaluationService)

    high_score, _ = service._score_answer(
        actual_answer="Audit history is stored in PostgreSQL. [C1]",
        expected_answer="Audit history should be stored in PostgreSQL.",
        citations_count=1,
        retrieved_chunks_count=1,
        citation_validation_score=1.0,
    )

    low_score, _ = service._score_answer(
        actual_answer="Audit history is stored in PostgreSQL. [C1]",
        expected_answer="Audit history should be stored in PostgreSQL.",
        citations_count=1,
        retrieved_chunks_count=1,
        citation_validation_score=0.0,
    )

    assert high_score > low_score
