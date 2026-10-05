from app.db.models import LLMCallLog, QueryAudit


class AuditService:
    def __init__(self, db):
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
        retrieval_mode: str | None = None,
        query_filters: dict | None = None,
    ) -> QueryAudit:
        audit = QueryAudit(
            request_id=request_id,
            query_text=query_text,
            retrieval_top_k=retrieval_top_k,
            retrieval_mode=retrieval_mode,
            query_filters=query_filters or {},
            retrieved_chunk_ids=retrieved_chunk_ids,
            answer_text=answer_text,
            model_name=model_name,
            latency_ms=latency_ms,
            token_estimate=token_estimate,
        )

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        return audit

    def get_query_audit(self, request_id: str) -> QueryAudit | None:
        return (
            self.db.query(QueryAudit)
            .filter(QueryAudit.request_id == request_id)
            .first()
        )

    def record_llm_call(
        self,
        request_id: str,
        purpose: str,
        model_name: str,
        input_token_estimate: int,
        output_token_estimate: int,
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
