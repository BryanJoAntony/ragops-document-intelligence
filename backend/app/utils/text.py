import re


def normalize_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def estimate_tokens(text: str) -> int:
    # Rough estimate good enough for chunk sizing before tokenizer-specific logic is added.
    return max(1, len(text) // 4)


def text_preview(text: str, max_chars: int = 160) -> str:
    normalized = normalize_whitespace(text).replace("\n", " ")
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."