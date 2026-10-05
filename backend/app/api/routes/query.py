from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.query import (
    AnswerMetadataResponse,
    CitationResponse,
    ProviderOutputResponse,
    QueryAnswerResponse,
    QueryAskRequest,
    QueryAuditResponse,
)
from app.services.audit_service import AuditService
from app.services.rag_query_service import RagQueryService

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/ask", response_model=QueryAnswerResponse)
def ask_question(
    request: QueryAskRequest,
    db: Session = Depends(get_db),
) -> QueryAnswerResponse:
    service = RagQueryService(db)

    try:
        request_id, orchestrated_answer, retrieved_chunks, latency_ms, retrieval_mode = service.ask(
            question=request.question,
            top_k=request.top_k,
            document_id=request.document_id,
            filters=request.filters,
            retrieval_mode=request.retrieval_mode,
            answer_strategy=request.answer_strategy,
            answer_provider=request.answer_provider,
            answer_providers=request.answer_providers,
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Answer provider failed: {exc}") from exc

    final_answer = orchestrated_answer.final_answer
    filter_payload = request.filters.model_dump(mode="json", exclude_none=True) if request.filters else {}

    citations = [
        CitationResponse(
            citation_id=citation.citation_id,
            document_id=citation.chunk.document_id,
            chunk_id=citation.chunk.chunk_id,
            chunk_index=citation.chunk.chunk_index,
            page_number=citation.chunk.metadata.get("page_number"),
            section_title=citation.chunk.metadata.get("section_title"),
            score=citation.chunk.score,
            text_preview=citation.chunk.text_preview,
        )
        for citation in final_answer.citations
    ]

    provider_outputs = [
        ProviderOutputResponse(
            answer_provider=provider_output.provider,
            model_name=provider_output.model_name,
            answer=provider_output.answer,
            citations_used=len(provider_output.citations),
            input_token_estimate=provider_output.input_token_estimate,
            output_token_estimate=provider_output.output_token_estimate,
            total_token_estimate=provider_output.total_token_estimate,
            estimated_cost_usd=provider_output.estimated_cost_usd,
        )
        for provider_output in orchestrated_answer.provider_outputs
    ]

    return QueryAnswerResponse(
        request_id=request_id,
        question=request.question,
        answer=final_answer.answer,
        citations=citations,
        retrieval={
            "mode": retrieval_mode,
            "top_k": request.top_k,
            "filters": filter_payload,
            "retrieved_chunks": len(retrieved_chunks),
            "citations_used": len(citations),
            "score_details": [
                chunk.metadata.get("score_details", {})
                for chunk in retrieved_chunks
            ],
        },
        answer_metadata=AnswerMetadataResponse(
            answer_provider=final_answer.provider,
            answer_strategy=orchestrated_answer.answer_strategy,
            provider_count=len(orchestrated_answer.provider_outputs),
            input_token_estimate=final_answer.input_token_estimate,
            output_token_estimate=final_answer.output_token_estimate,
            total_token_estimate=final_answer.total_token_estimate,
            estimated_cost_usd=final_answer.estimated_cost_usd,
        ),
        provider_outputs=provider_outputs,
        model_name=final_answer.model_name,
        latency_ms=latency_ms,
    )


@router.get("/audits/{request_id}", response_model=QueryAuditResponse)
def get_query_audit(
    request_id: str,
    db: Session = Depends(get_db),
) -> QueryAuditResponse:
    service = AuditService(db)
    audit = service.get_query_audit(request_id)

    if audit is None:
        raise HTTPException(status_code=404, detail="Query audit not found.")

    return QueryAuditResponse(
        request_id=audit.request_id,
        query_text=audit.query_text,
        retrieval_top_k=audit.retrieval_top_k,
        retrieval_mode=audit.retrieval_mode,
        query_filters=audit.query_filters,
        retrieved_chunk_ids=audit.retrieved_chunk_ids,
        answer_text=audit.answer_text,
        model_name=audit.model_name,
        latency_ms=audit.latency_ms,
        token_estimate=audit.token_estimate,
        created_at=audit.created_at,
    )

