import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.query import RetrievalFilters
from app.services.answer_orchestration_service import AnswerOrchestrationService, OrchestratedAnswer
from app.services.audit_service import AuditService
from app.services.retrieval_service import RetrievedChunk, RetrievalService
from app.utils.ids import new_request_id


class RagQueryService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.retrieval_service = RetrievalService(db)
        self.answer_orchestration_service = AnswerOrchestrationService()
        self.audit_service = AuditService(db)

    def ask(
        self,
        question: str,
        top_k: int,
        document_id: UUID | None = None,
        filters: RetrievalFilters | dict | None = None,
        retrieval_mode: str | None = None,
        answer_strategy: str = "single",
        answer_provider: str | None = None,
        answer_providers: list[str] | None = None,
    ) -> tuple[str, OrchestratedAnswer, list[RetrievedChunk], int, str]:
        request_id = new_request_id()
        start_time = time.perf_counter()
        mode = retrieval_mode or self.settings.default_retrieval_mode

        try:
            chunks = self.retrieval_service.search(
                query=question,
                top_k=top_k,
                document_id=document_id,
                filters=filters,
                retrieval_mode=mode,
            )

            orchestrated_answer = self.answer_orchestration_service.generate(
                question=question,
                chunks=chunks,
                answer_strategy=answer_strategy,
                answer_provider=answer_provider,
                answer_providers=answer_providers,
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            retrieved_chunk_ids = [str(chunk.chunk_id) for chunk in chunks]
            final_answer = orchestrated_answer.final_answer

            self.audit_service.record_query_audit(
                request_id=request_id,
                query_text=question,
                retrieval_top_k=top_k,
                retrieval_mode=mode,
                query_filters=self._serialize_filters(filters),
                retrieved_chunk_ids=retrieved_chunk_ids,
                answer_text=final_answer.answer,
                model_name=final_answer.model_name,
                latency_ms=latency_ms,
                token_estimate=final_answer.total_token_estimate,
            )

            self._record_provider_call_logs(
                request_id=request_id,
                orchestrated_answer=orchestrated_answer,
                latency_ms=latency_ms,
            )

            return request_id, orchestrated_answer, chunks, latency_ms, mode

        except Exception:
            raise

    def _record_provider_call_logs(
        self,
        request_id: str,
        orchestrated_answer: OrchestratedAnswer,
        latency_ms: int,
    ) -> None:
        purpose = (
            "answer_generation_compare"
            if orchestrated_answer.answer_strategy == "compare"
            else "answer_generation_single"
        )

        for provider_output in orchestrated_answer.provider_outputs:
            self.audit_service.record_llm_call(
                request_id=request_id,
                purpose=purpose,
                model_name=provider_output.model_name,
                input_token_estimate=provider_output.input_token_estimate,
                output_token_estimate=provider_output.output_token_estimate,
                latency_ms=latency_ms,
                status="success",
            )

    @staticmethod
    def _serialize_filters(filters: RetrievalFilters | dict | None) -> dict:
        if filters is None:
            return {}

        if isinstance(filters, RetrievalFilters):
            return filters.model_dump(mode="json", exclude_none=True)

        return {
            key: str(value)
            for key, value in dict(filters).items()
            if value is not None
        }
