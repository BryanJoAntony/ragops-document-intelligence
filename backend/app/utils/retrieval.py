import re
from collections.abc import Iterable


def tokenize_for_retrieval(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def normalize_scores(raw_scores: Iterable[float]) -> list[float]:
    scores = [float(score) for score in raw_scores]

    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return [1.0 if max_score > 0 else 0.0 for _ in scores]

    return [(score - min_score) / (max_score - min_score) for score in scores]


def clamp_score(score: float) -> float:
    return max(0.0, min(1.0, score))