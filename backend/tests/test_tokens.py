from app.core.pricing import estimate_cost_usd
from app.utils.tokens import estimate_messages_tokens, estimate_tokens


def test_estimate_tokens_handles_empty_text() -> None:
    assert estimate_tokens("") == 0


def test_estimate_tokens_returns_positive_for_text() -> None:
    assert estimate_tokens("hello world") > 0


def test_estimate_messages_tokens_counts_messages() -> None:
    messages = [
        {"role": "system", "content": "You are careful."},
        {"role": "user", "content": "Answer with citations."},
    ]

    assert estimate_messages_tokens(messages) > 0


def test_estimate_cost_usd_for_local_model_is_zero() -> None:
    assert estimate_cost_usd("local_extractive_v1", 1000, 1000) == 0.0


def test_estimate_cost_usd_for_openai_model_is_positive() -> None:
    assert estimate_cost_usd("gpt-4o-mini", 1000, 1000) > 0.0