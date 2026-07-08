from dataclasses import dataclass

from openai import OpenAI

from app.core.config import get_settings
from app.core.pricing import estimate_cost_usd
from app.services.retrieval_service import RetrievedChunk
from app.utils.text import normalize_whitespace
from app.utils.tokens import estimate_messages_tokens, estimate_tokens


@dataclass(frozen=True)
class Citation:
    citation_id: str
    chunk: RetrievedChunk


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    citations: list[Citation]
    model_name: str
    input_token_estimate: int
    output_token_estimate: int
    total_token_estimate: int
    estimated_cost_usd: float
    provider: str


class AnswerGenerationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        answer_provider: str | None = None,
    ) -> GeneratedAnswer:
        provider = (answer_provider or self.settings.default_answer_provider).lower().strip()

        if provider == "local_extractive":
            return self._generate_local_extractive_answer(question=question, chunks=chunks)

        if provider == "openai":
            return self._generate_openai_answer(question=question, chunks=chunks)

        raise NotImplementedError(f"Answer provider '{provider}' is not implemented yet.")

    def _generate_openai_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when answer_provider=openai.")

        if not chunks:
            return self._generate_no_context_answer(question=question, provider="openai")

        selected_chunks = chunks[: self.settings.max_context_chunks] if hasattr(self.settings, "max_context_chunks") else chunks[:5]
        citations = [
            Citation(citation_id=f"C{i + 1}", chunk=chunk)
            for i, chunk in enumerate(selected_chunks)
        ]

        messages = self._build_openai_messages(question=question, citations=citations)
        input_tokens = estimate_messages_tokens(messages)

        client = OpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.openai_timeout_seconds,
        )

        response = client.chat.completions.create(
            model=self.settings.openai_answer_model,
            messages=messages,
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.openai_max_output_tokens,
        )

        answer = (response.choices[0].message.content or "").strip()

        usage = response.usage
        if usage is not None:
            input_tokens = usage.prompt_tokens or input_tokens
            output_tokens = usage.completion_tokens or estimate_tokens(answer)
        else:
            output_tokens = estimate_tokens(answer)

        total_tokens = input_tokens + output_tokens
        estimated_cost = estimate_cost_usd(
            model_name=self.settings.openai_answer_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return GeneratedAnswer(
            answer=answer,
            citations=citations,
            model_name=self.settings.openai_answer_model,
            input_token_estimate=input_tokens,
            output_token_estimate=output_tokens,
            total_token_estimate=total_tokens,
            estimated_cost_usd=estimated_cost,
            provider="openai",
        )

    def _generate_local_extractive_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        if not chunks:
            return self._generate_no_context_answer(question=question, provider="local_extractive")

        selected_chunks = chunks[:5]
        citations = [
            Citation(citation_id=f"C{i + 1}", chunk=chunk)
            for i, chunk in enumerate(selected_chunks)
        ]

        answer = self._build_extractive_answer(question, citations)
        input_tokens = estimate_tokens(question + "\n".join(chunk.chunk_text for chunk in selected_chunks))
        output_tokens = estimate_tokens(answer)
        total_tokens = input_tokens + output_tokens

        return GeneratedAnswer(
            answer=answer,
            citations=citations,
            model_name=self.settings.local_answer_model,
            input_token_estimate=input_tokens,
            output_token_estimate=output_tokens,
            total_token_estimate=total_tokens,
            estimated_cost_usd=0.0,
            provider="local_extractive",
        )

    def _generate_no_context_answer(self, question: str, provider: str) -> GeneratedAnswer:
        answer = (
            "I could not find enough indexed context to answer this question. "
            "Try ingesting and indexing relevant documents first."
        )

        input_tokens = estimate_tokens(question)
        output_tokens = estimate_tokens(answer)

        if provider == "openai":
            model_name = self.settings.openai_answer_model
            estimated_cost = estimate_cost_usd(
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        else:
            model_name = self.settings.local_answer_model
            estimated_cost = 0.0

        return GeneratedAnswer(
            answer=answer,
            citations=[],
            model_name=model_name,
            input_token_estimate=input_tokens,
            output_token_estimate=output_tokens,
            total_token_estimate=input_tokens + output_tokens,
            estimated_cost_usd=estimated_cost,
            provider=provider,
        )

    def _build_openai_messages(
        self,
        question: str,
        citations: list[Citation],
    ) -> list[dict[str, str]]:
        context_blocks = []

        for citation in citations:
            chunk = citation.chunk
            context_blocks.append(
                "\n".join(
                    [
                        f"[{citation.citation_id}]",
                        f"document_id: {chunk.document_id}",
                        f"chunk_id: {chunk.chunk_id}",
                        f"section_title: {chunk.metadata.get('section_title')}",
                        f"score: {chunk.score}",
                        "text:",
                        chunk.chunk_text,
                    ]
                )
            )

        context = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are a careful RAG answer generator for a document intelligence system. "
            "Answer only using the provided context. Every factual claim must include a citation marker "
            "like [C1]. If the context is insufficient, say what is missing. Do not invent facts."
        )

        user_prompt = (
            f"Question:\n{question}\n\n"
            f"Retrieved context:\n{context}\n\n"
            "Return a concise answer. Use citation markers from the context."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_extractive_answer(self, question: str, citations: list[Citation]) -> str:
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