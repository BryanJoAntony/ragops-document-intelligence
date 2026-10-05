from dataclasses import dataclass

from app.core.config import get_settings
from app.services.answer_generation_service import AnswerGenerationService, GeneratedAnswer
from app.services.retrieval_service import RetrievedChunk


@dataclass(frozen=True)
class OrchestratedAnswer:
    final_answer: GeneratedAnswer
    provider_outputs: list[GeneratedAnswer]
    answer_strategy: str


class AnswerOrchestrationService:
    """
    Decides how answer providers are executed.

    This service owns strategy-level behavior:
    - single provider execution
    - compare execution across multiple providers

    It does not judge, rank, or combine provider outputs yet.
    For compare mode, the final answer is intentionally deterministic:
    the first provider output is selected as the final answer.
    """

    def __init__(self, answer_generation_service: AnswerGenerationService | None = None) -> None:
        self.settings = get_settings()
        self.answer_generation_service = answer_generation_service or AnswerGenerationService()

    def generate(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        answer_strategy: str = "single",
        answer_provider: str | None = None,
        answer_providers: list[str] | None = None,
    ) -> OrchestratedAnswer:
        strategy = answer_strategy.lower().strip()

        if strategy == "single":
            return self._generate_single(
                question=question,
                chunks=chunks,
                answer_provider=answer_provider,
            )

        if strategy == "compare":
            return self._generate_compare(
                question=question,
                chunks=chunks,
                answer_providers=answer_providers,
            )

        raise ValueError(f"Unsupported answer_strategy '{answer_strategy}'.")

    def _generate_single(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        answer_provider: str | None,
    ) -> OrchestratedAnswer:
        generated_answer = self.answer_generation_service.generate_answer(
            question=question,
            chunks=chunks,
            answer_provider=answer_provider,
        )

        return OrchestratedAnswer(
            final_answer=generated_answer,
            provider_outputs=[generated_answer],
            answer_strategy="single",
        )

    def _generate_compare(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        answer_providers: list[str] | None,
    ) -> OrchestratedAnswer:
        if not answer_providers:
            raise ValueError("answer_providers is required when answer_strategy=compare.")

        unique_providers = list(dict.fromkeys(provider.lower().strip() for provider in answer_providers))
        if len(unique_providers) < 2:
            raise ValueError("answer_strategy=compare requires at least 2 unique providers.")

        provider_outputs = [
            self.answer_generation_service.generate_answer(
                question=question,
                chunks=chunks,
                answer_provider=provider,
            )
            for provider in unique_providers
        ]

        return OrchestratedAnswer(
            final_answer=provider_outputs[0],
            provider_outputs=provider_outputs,
            answer_strategy="compare",
        )
