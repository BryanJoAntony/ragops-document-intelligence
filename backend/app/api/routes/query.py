from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.query import (
    CitationResponse,
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
        request_id, generated_answer, retrieved_chunks, latency_ms = service.ask(
            question=request.question,
            top_k=request.top_k,
            document_id=request.document_id,
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

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
        for citation in generated_answer.citations
    ]

    return QueryAnswerResponse(
        request_id=request_id,
        question=request.question,
        answer=generated_answer.answer,
        citations=citations,
        retrieval={
            "top_k": request.top_k,
            "retrieved_chunks": len(retrieved_chunks),
            "citations_used": len(citations),
        },
        model_name=generated_answer.model_name,
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
        retrieved_chunk_ids=audit.retrieved_chunk_ids,
        answer_text=audit.answer_text,
        model_name=audit.model_name,
        latency_ms=audit.latency_ms,
        token_estimate=audit.token_estimate,
        created_at=audit.created_at,
    )