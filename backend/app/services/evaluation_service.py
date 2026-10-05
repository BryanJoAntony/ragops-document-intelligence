from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EvaluationResult, EvaluationRun
from app.services.citation_validation_service import CitationValidationService
from app.services.rag_query_service import RagQueryService


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.rag_query_service = RagQueryService(db)
        self.citation_validation_service = CitationValidationService(db)

    def run_evaluation(
        self,
        run_name: str,
        questions: list,
        retrieval_mode: str,
        top_k: int,
        answer_strategy: str,
        answer_provider: str | None = None,
        answer_providers: list[str] | None = None,
    ) -> EvaluationRun:
        run = EvaluationRun(
            run_name=run_name,
            retrieval_mode=retrieval_mode,
            answer_strategy=answer_strategy,
            answer_provider=answer_provider,
            answer_providers=answer_providers,
            total_questions=len(questions),
            status="running",
            run_metadata={
                "evaluator": "local_deterministic_v2_with_citation_validation",
                "metrics": [
                    "has_answer",
                    "has_citations",
                    "retrieved_chunks_count",
                    "citations_count",
                    "expected_answer_keyword_overlap",
                    "citation_validation_score",
                    "combined_score",
                ],
            },
        )
        self.db.add(run)
        self.db.flush()

        scores: list[float] = []

        for item in questions:
            request_id, orchestrated_answer, chunks, latency_ms, used_retrieval_mode = self.rag_query_service.ask(
                question=item.question,
                top_k=top_k,
                document_id=item.document_id,
                retrieval_mode=retrieval_mode,
                answer_strategy=answer_strategy,
                answer_provider=answer_provider,
                answer_providers=answer_providers,
            )

            final_answer = orchestrated_answer.final_answer
            citations_count = len(final_answer.citations)
            retrieved_chunks_count = len(chunks)

            citation_validation = self.citation_validation_service.validate_generated_answer(
                request_id=request_id,
                question=item.question,
                generated_answer=final_answer,
                latency_ms=latency_ms,
                retrieval_mode=used_retrieval_mode,
                answer_strategy=orchestrated_answer.answer_strategy,
                provider_count=len(orchestrated_answer.provider_outputs),
            )

            score, details = self._score_answer(
                actual_answer=final_answer.answer,
                expected_answer=item.expected_answer,
                citations_count=citations_count,
                retrieved_chunks_count=retrieved_chunks_count,
                citation_validation_score=citation_validation.validation_score,
            )
            scores.append(score)

            result = EvaluationResult(
                run_id=run.id,
                request_id=request_id,
                question=item.question,
                expected_answer=item.expected_answer,
                actual_answer=final_answer.answer,
                score=score,
                retrieved_chunks_count=retrieved_chunks_count,
                citations_count=citations_count,
                evaluation_details={
                    **details,
                    "latency_ms": latency_ms,
                    "retrieval_mode": used_retrieval_mode,
                    "answer_provider": final_answer.provider,
                    "answer_strategy": orchestrated_answer.answer_strategy,
                    "provider_count": len(orchestrated_answer.provider_outputs),
                    "citation_validation": {
                        "validation_id": str(citation_validation.validation_id),
                        "validation_score": citation_validation.validation_score,
                        "citation_markers_found": citation_validation.citation_markers_found,
                        "citations_provided_count": citation_validation.citations_provided_count,
                        "cited_claims_count": citation_validation.cited_claims_count,
                        "supported_claims_count": citation_validation.supported_claims_count,
                        "unsupported_claims_count": citation_validation.unsupported_claims_count,
                    },
                },
            )
            self.db.add(result)

        run.average_score = round(sum(scores) / len(scores), 4) if scores else 0.0
        run.status = "completed"
        self.db.commit()
        self.db.refresh(run)

        return run

    def get_run(self, run_id: UUID) -> EvaluationRun | None:
        return self.db.get(EvaluationRun, run_id)

    def _score_answer(
        self,
        actual_answer: str | None,
        expected_answer: str | None,
        citations_count: int,
        retrieved_chunks_count: int,
        citation_validation_score: float | None = None,
    ) -> tuple[float, dict]:
        has_answer = bool(actual_answer and actual_answer.strip())
        has_citations = citations_count > 0
        has_retrieved_context = retrieved_chunks_count > 0
        citation_score = citation_validation_score if citation_validation_score is not None else 0.0

        score_parts = {
            "has_answer": 1.0 if has_answer else 0.0,
            "has_citations": 1.0 if has_citations else 0.0,
            "has_retrieved_context": 1.0 if has_retrieved_context else 0.0,
            "expected_answer_keyword_overlap": 0.0,
            "citation_validation_score": citation_score,
        }

        if expected_answer and actual_answer:
            expected_terms = self._important_terms(expected_answer)
            actual_terms = self._important_terms(actual_answer)

            if expected_terms:
                overlap = len(expected_terms.intersection(actual_terms)) / len(expected_terms)
                score_parts["expected_answer_keyword_overlap"] = round(overlap, 4)

        if expected_answer:
            weights = {
                "has_answer": 0.20,
                "has_citations": 0.15,
                "has_retrieved_context": 0.15,
                "expected_answer_keyword_overlap": 0.25,
                "citation_validation_score": 0.25,
            }
        else:
            weights = {
                "has_answer": 0.30,
                "has_citations": 0.20,
                "has_retrieved_context": 0.20,
                "expected_answer_keyword_overlap": 0.0,
                "citation_validation_score": 0.30,
            }

        score = sum(score_parts[key] * weight for key, weight in weights.items())

        return round(score, 4), {
            "score_parts": score_parts,
            "weights": weights,
            "evaluator": "local_deterministic_v2_with_citation_validation",
        }

    @staticmethod
    def _important_terms(text: str) -> set[str]:
        stopwords = {
            "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
            "with", "is", "are", "was", "were", "be", "by", "as", "it",
            "this", "that", "should", "from", "into",
        }

        cleaned = "".join(
            char.lower() if char.isalnum() else " "
            for char in text
        )

        return {
            token
            for token in cleaned.split()
            if len(token) >= 4 and token not in stopwords
        }
