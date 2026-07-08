from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    input_per_1m_tokens_usd: float
    output_per_1m_tokens_usd: float


MODEL_PRICING_USD: dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(
        input_per_1m_tokens_usd=0.15,
        output_per_1m_tokens_usd=0.60,
    ),
    "local_extractive_v1": ModelPricing(
        input_per_1m_tokens_usd=0.0,
        output_per_1m_tokens_usd=0.0,
    ),
}


def estimate_cost_usd(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    pricing = MODEL_PRICING_USD.get(model_name)

    if pricing is None:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing.input_per_1m_tokens_usd
    output_cost = (output_tokens / 1_000_000) * pricing.output_per_1m_tokens_usd

    return round(input_cost + output_cost, 8)