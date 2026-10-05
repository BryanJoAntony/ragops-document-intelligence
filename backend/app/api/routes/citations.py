from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.citations import (
    CitationValidationResponse,
    CitationValidationRunRequest,
    ClaimValidationResponse,
    ValidatedCitationResponse,
)
from app.services.citation_validation_service import CitationValidationService

router = APIRouter(prefix="/citations", tags=["citations"])


@router.post("/validate-rag", response_model=CitationValidationResponse)
def validate_rag_citations(
    request: CitationValidationRunRequest,
    db: Session = Depends(get_db),
) -> CitationValidationResponse:
    service = CitationValidationService(db)

    try:
        result = service.validate_rag_answer(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k,
            retrieval_mode=request.retrieval_mode,
            answer_strategy=request.answer_strategy,
            answer_provider=request.answer_provider,
            answer_providers=request.answer_providers,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return CitationValidationResponse(
        validation_id=result.validation_id,
        request_id=result.request_id,
        question=result.question,
        answer=result.answer,
        validation_score=result.validation_score,
        citation_markers_found=result.citation_markers_found,
        citations_provided_count=result.citations_provided_count,
        cited_claims_count=result.cited_claims_count,
        supported_claims_count=result.supported_claims_count,
        unsupported_claims_count=result.unsupported_claims_count,
        validated_citations=[
            ValidatedCitationResponse(
                citation_id=item.citation_id,
                citation_marker=item.citation_marker,
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                marker_found_in_answer=item.marker_found_in_answer,
                citation_provided=item.citation_provided,
            )
            for item in result.validated_citations
        ],
        claim_validations=[
            ClaimValidationResponse(
                claim_text=item.claim_text,
                citation_marker=item.citation_marker,
                citation_id=item.citation_id,
                supported=item.supported,
                support_score=item.support_score,
                reason=item.reason,
            )
            for item in result.claim_validations
        ],
        validation_details=result.validation_details,
    )
