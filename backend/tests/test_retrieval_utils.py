from app.utils.retrieval import clamp_score, normalize_scores, tokenize_for_retrieval


def test_tokenize_for_retrieval_lowercases_and_splits() -> None:
    tokens = tokenize_for_retrieval("Audit history should be stored in PostgreSQL.")

    assert tokens == ["audit", "history", "should", "be", "stored", "in", "postgresql"]


def test_normalize_scores_scales_values() -> None:
    scores = normalize_scores([2.0, 4.0, 6.0])

    assert scores == [0.0, 0.5, 1.0]


def test_normalize_scores_handles_equal_values() -> None:
    scores = normalize_scores([3.0, 3.0, 3.0])

    assert scores == [1.0, 1.0, 1.0]


def test_clamp_score_limits_range() -> None:
    assert clamp_score(-0.5) == 0.0
    assert clamp_score(1.5) == 1.0
    assert clamp_score(0.7) == 0.7