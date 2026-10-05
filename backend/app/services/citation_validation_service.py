import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import CitationValidationResult
from app.services.answer_generation_service import GeneratedAnswer
from app.services.rag_query_service import RagQueryService


@dataclass(frozen=True)
class ValidatedCitation:
    citation_id: str
    citation_marker: str
    chunk_id: UUID | None
    document_id: UUID | None
    marker_found_in_answer: bool
    citation_provided: bool


@dataclass(frozen=True)
class ClaimValidation:
    claim_text: str
    citation_marker: str | None
    citation_id: str | None
    supported: bool
    support_score: float
    reason: str


@dataclass(frozen=True)
class CitationValidationOutput:
    validation_id: UUID
    request_id: str
    question: str
    answer: str
    validation_score: float
    citation_markers_found: list[str]
    citations_provided_count: int
    cited_claims_count: int
    supported_claims_count: int
    unsupported_claims_count: int
    validated_citations: list[ValidatedCitation]
    claim_validations: list[ClaimValidation]
    validation_details: dict


class CitationValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.rag_query_service = RagQueryService(db)

    def validate_rag_answer(
        self,
        question: str,
        top_k: int,
        document_id: UUID | None = None,
        retrieval_mode: str = "hybrid",
        answer_strategy: str = "single",
        answer_provider: str | None = None,
        answer_providers: list[str] | None = None,
    ) -> CitationValidationOutput:
        request_id, orchestrated_answer, chunks, latency_ms, used_retrieval_mode = self.rag_query_service.ask(
            question=question,
            top_k=top_k,
            document_id=document_id,
            retrieval_mode=retrieval_mode,
            answer_strategy=answer_strategy,
            answer_provider=answer_provider,
            answer_providers=answer_providers,
        )

        final_answer = orchestrated_answer.final_answer

        return self.validate_generated_answer(
            request_id=request_id,
            question=question,
            generated_answer=final_answer,
            latency_ms=latency_ms,
            retrieval_mode=used_retrieval_mode,
            answer_strategy=orchestrated_answer.answer_strategy,
            provider_count=len(orchestrated_answer.provider_outputs),
        )

    def validate_generated_answer(
        self,
        request_id: str,
        question: str,
        generated_answer: GeneratedAnswer,
        latency_ms: int | None = None,
        retrieval_mode: str | None = None,
        answer_strategy: str | None = None,
        provider_count: int | None = None,
    ) -> CitationValidationOutput:
        answer_text = generated_answer.answer
        citation_markers_found = self._extract_citation_markers(answer_text)
        citation_map = {
            citation.citation_id: citation
            for citation in generated_answer.citations
        }

        validated_citations = self._validate_citation_markers(
            citation_markers_found=citation_markers_found,
            citation_map=citation_map,
        )

        claim_validations = self._validate_claims(
            answer_text=answer_text,
            citation_map=citation_map,
        )

        cited_claims_count = len(claim_validations)
        supported_claims_count = sum(1 for claim in claim_validations if claim.supported)
        unsupported_claims_count = cited_claims_count - supported_claims_count

        validation_score = self._calculate_validation_score(
            citation_markers_found=citation_markers_found,
            citations_provided_count=len(generated_answer.citations),
            cited_claims_count=cited_claims_count,
            supported_claims_count=supported_claims_count,
        )

        details = {
            "validator": "local_citation_validator_v1",
            "latency_ms": latency_ms,
            "retrieval_mode": retrieval_mode,
            "answer_strategy": answer_strategy,
            "answer_provider": generated_answer.provider,
            "provider_count": provider_count,
            "model_name": generated_answer.model_name,
            "rules": {
                "marker_pattern": "[C<number>]",
                "claim_support_method": "keyword_overlap_against_cited_chunk",
                "support_threshold": 0.30,
            },
        }

        db_result = CitationValidationResult(
            request_id=request_id,
            question=question,
            answer_text=answer_text,
            citation_markers_found=citation_markers_found,
            citations_provided_count=len(generated_answer.citations),
            cited_claims_count=cited_claims_count,
            supported_claims_count=supported_claims_count,
            unsupported_claims_count=unsupported_claims_count,
            validation_score=validation_score,
            validation_details={
                **details,
                "validated_citations": [
                    {
                        "citation_id": item.citation_id,
                        "citation_marker": item.citation_marker,
                        "chunk_id": str(item.chunk_id) if item.chunk_id else None,
                        "document_id": str(item.document_id) if item.document_id else None,
                        "marker_found_in_answer": item.marker_found_in_answer,
                        "citation_provided": item.citation_provided,
                    }
                    for item in validated_citations
                ],
                "claim_validations": [
                    {
                        "claim_text": claim.claim_text,
                        "citation_marker": claim.citation_marker,
                        "citation_id": claim.citation_id,
                        "supported": claim.supported,
                        "support_score": claim.support_score,
                        "reason": claim.reason,
                    }
                    for claim in claim_validations
                ],
            },
        )
        self.db.add(db_result)
        self.db.commit()
        self.db.refresh(db_result)

        return CitationValidationOutput(
            validation_id=db_result.id,
            request_id=request_id,
            question=question,
            answer=answer_text,
            validation_score=validation_score,
            citation_markers_found=citation_markers_found,
            citations_provided_count=len(generated_answer.citations),
            cited_claims_count=cited_claims_count,
            supported_claims_count=supported_claims_count,
            unsupported_claims_count=unsupported_claims_count,
            validated_citations=validated_citations,
            claim_validations=claim_validations,
            validation_details=details,
        )

    def _validate_citation_markers(
        self,
        citation_markers_found: list[str],
        citation_map: dict,
    ) -> list[ValidatedCitation]:
        results: list[ValidatedCitation] = []

        for marker in citation_markers_found:
            citation_id = marker.strip("[]")
            citation = citation_map.get(citation_id)

            if citation is None:
                results.append(
                    ValidatedCitation(
                        citation_id=citation_id,
                        citation_marker=marker,
                        chunk_id=None,
                        document_id=None,
                        marker_found_in_answer=True,
                        citation_provided=False,
                    )
                )
                continue

            results.append(
                ValidatedCitation(
                    citation_id=citation_id,
                    citation_marker=marker,
                    chunk_id=citation.chunk.chunk_id,
                    document_id=citation.chunk.document_id,
                    marker_found_in_answer=True,
                    citation_provided=True,
                )
            )

        return results

    def _validate_claims(
        self,
        answer_text: str,
        citation_map: dict,
    ) -> list[ClaimValidation]:
        claims = self._extract_cited_claims(answer_text)
        results: list[ClaimValidation] = []

        for claim_text, marker in claims:
            citation_id = marker.strip("[]") if marker else None
            citation = citation_map.get(citation_id) if citation_id else None

            if citation is None:
                results.append(
                    ClaimValidation(
                        claim_text=claim_text,
                        citation_marker=marker,
                        citation_id=citation_id,
                        supported=False,
                        support_score=0.0,
                        reason="Citation marker does not map to a provided citation.",
                    )
                )
                continue

            support_score = self._keyword_overlap_score(
                claim_text=claim_text,
                evidence_text=citation.chunk.chunk_text,
            )
            supported = support_score >= 0.30

            results.append(
                ClaimValidation(
                    claim_text=claim_text,
                    citation_marker=marker,
                    citation_id=citation_id,
                    supported=supported,
                    support_score=support_score,
                    reason=(
                        "Claim has enough keyword overlap with cited chunk."
                        if supported
                        else "Claim has weak keyword overlap with cited chunk."
                    ),
                )
            )

        return results

    @staticmethod
    def _extract_citation_markers(answer_text: str) -> list[str]:
        markers = re.findall(r"\[C\d+\]", answer_text)
        return list(dict.fromkeys(markers))

    @staticmethod
    def _extract_cited_claims(answer_text: str) -> list[tuple[str, str]]:
        claim_lines: list[tuple[str, str]] = []

        for line in answer_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            marker_match = re.search(r"\[C\d+\]", stripped)
            if not marker_match:
                continue

            marker = marker_match.group(0)
            claim_text = stripped.replace(marker, "").strip(" -")
            if claim_text:
                claim_lines.append((claim_text, marker))

        return claim_lines

    @staticmethod
    def _keyword_overlap_score(claim_text: str, evidence_text: str) -> float:
        claim_terms = CitationValidationService._important_terms(claim_text)
        evidence_terms = CitationValidationService._important_terms(evidence_text)

        if not claim_terms:
            return 0.0

        overlap = len(claim_terms.intersection(evidence_terms)) / len(claim_terms)
        return round(overlap, 4)

    @staticmethod
    def _important_terms(text: str) -> set[str]:
        stopwords = {
            "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
            "with", "is", "are", "was", "were", "be", "by", "as", "it",
            "this", "that", "should", "from", "into", "based", "retrieved",
            "document", "context", "answer", "only", "uses", "cited",
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

    @staticmethod
    def _calculate_validation_score(
        citation_markers_found: list[str],
        citations_provided_count: int,
        cited_claims_count: int,
        supported_claims_count: int,
    ) -> float:
        has_markers = 1.0 if citation_markers_found else 0.0
        has_provided_citations = 1.0 if citations_provided_count > 0 else 0.0

        if cited_claims_count > 0:
            support_ratio = supported_claims_count / cited_claims_count
        else:
            support_ratio = 0.0

        score = (
            (0.30 * has_markers)
            + (0.30 * has_provided_citations)
            + (0.40 * support_ratio)
        )

        return round(score, 4)
