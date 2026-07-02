import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LLMCallLog, QueryAudit

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record_query_audit(
        self,
        request_id: str,
        query_text: str,
        retrieval_top_k: int,
        retrieved_chunk_ids: list[str],
        answer_text: str | None,
        model_name: str | None,
        latency_ms: int | None,
        token_estimate: int | None,
    ) -> QueryAudit:
        audit = QueryAudit(
            request_id=request_id,
            query_text=query_text,
            retrieval_top_k=retrieval_top_k,
            retrieved_chunk_ids=retrieved_chunk_ids,
            answer_text=answer_text,
            model_name=model_name,
            latency_ms=latency_ms,
            token_estimate=token_estimate,
        )

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        logger.info(
            "Query audit recorded",
            extra={
                "request_id": request_id,
                "retrieved_chunk_count": len(retrieved_chunk_ids),
                "model_name": model_name,
            },
        )

        return audit

    def record_llm_call(
        self,
        request_id: str,
        purpose: str,
        model_name: str,
        input_token_estimate: int | None,
        output_token_estimate: int | None,
        latency_ms: int | None,
        status: str,
        error_message: str | None = None,
    ) -> LLMCallLog:
        call_log = LLMCallLog(
            request_id=request_id,
            purpose=purpose,
            model_name=model_name,
            input_token_estimate=input_token_estimate,
            output_token_estimate=output_token_estimate,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
        )

        self.db.add(call_log)
        self.db.commit()
        self.db.refresh(call_log)

        return call_log

    def get_query_audit(self, request_id: str) -> QueryAudit | None:
        statement = select(QueryAudit).where(QueryAudit.request_id == request_id)
        return self.db.scalars(statement).first()