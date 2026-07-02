from dataclasses import dataclass

from app.core.config import get_settings
from app.services.retrieval_service import RetrievedChunk
from app.utils.text import estimate_tokens, normalize_whitespace


@dataclass(frozen=True)
class Citation:
    citation_id: str
    chunk: RetrievedChunk


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    citations: list[Citation]
    model_name: str
    token_estimate: int


class AnswerGenerationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = self.settings.answer_provider.lower().strip()

        if self.provider != "local_extractive":
            raise NotImplementedError(
                f"Answer provider '{self.settings.answer_provider}' is not implemented yet."
            )

    def generate_answer(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        if not chunks:
            return GeneratedAnswer(
                answer=(
                    "I could not find enough indexed context to answer this question. "
                    "Try ingesting and indexing relevant documents first."
                ),
                citations=[],
                model_name=self.settings.answer_model,
                token_estimate=estimate_tokens(question),
            )

        selected_chunks = chunks[: self.settings.max_context_chunks]
        citations = [
            Citation(citation_id=f"C{i + 1}", chunk=chunk)
            for i, chunk in enumerate(selected_chunks)
        ]

        answer = self._build_extractive_answer(question, citations)
        token_estimate = estimate_tokens(question + "\n" + answer)

        return GeneratedAnswer(
            answer=answer,
            citations=citations,
            model_name=self.settings.answer_model,
            token_estimate=token_estimate,
        )

    def _build_extractive_answer(self, question: str, citations: list[Citation]) -> str:
        # This v1 provider is intentionally conservative: every factual sentence is tied to a citation.
        lines = [
            f"Based on the retrieved document context, here is a grounded answer to: {question}",
            "",
        ]

        for citation in citations:
            chunk = citation.chunk
            evidence = self._first_useful_sentence(chunk.chunk_text)

            lines.append(f"- {evidence} [{citation.citation_id}]")

        lines.append("")
        lines.append(
            "This answer only uses the retrieved cited context. "
            "If the cited chunks are incomplete, the answer may also be incomplete."
        )

        return "\n".join(lines)

    @staticmethod
    def _first_useful_sentence(text: str) -> str:
        normalized = normalize_whitespace(text).replace("\n", " ")
        sentences = [part.strip() for part in normalized.split(".") if part.strip()]

        if not sentences:
            return normalized[:240]

        first_sentence = sentences[0]
        if len(first_sentence) > 280:
            return first_sentence[:277].rstrip() + "..."

        return first_sentence + "."