def estimate_tokens(text: str) -> int:
    if not text:
        return 0

    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    total = 0

    for message in messages:
        total += estimate_tokens(message.get("role", ""))
        total += estimate_tokens(message.get("content", ""))

    # Rough overhead estimate for chat-message formatting.
    return total + (len(messages) * 4)