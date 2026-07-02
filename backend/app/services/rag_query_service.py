import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.answer_generation_service import AnswerGenerationService, GeneratedAnswer
from app.services.audit_service import AuditService
from app.services.retrieval_service import RetrievedChunk, RetrievalService
from app.utils.ids import new_request_id
from app.utils.text import estimate_tokens


class RagQueryService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.retrieval_service = RetrievalService(db)
        self.answer_service = AnswerGenerationService()
        self.audit_service = AuditService(db)

    def ask(
        self,
        question: str,
        top_k: int,
        document_id=None,
    ) -> tuple[str, GeneratedAnswer, list[RetrievedChunk], int]:
        request_id = new_request_id()
        start_time = time.perf_counter()

        chunks = self.retrieval_service.vector_search(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        generated_answer = self.answer_service.generate_answer(
            question=question,
            chunks=chunks,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        retrieved_chunk_ids = [str(chunk.chunk_id) for chunk in chunks]

        self.audit_service.record_query_audit(
            request_id=request_id,
            query_text=question,
            retrieval_top_k=top_k,
            retrieved_chunk_ids=retrieved_chunk_ids,
            answer_text=generated_answer.answer,
            model_name=generated_answer.model_name,
            latency_ms=latency_ms,
            token_estimate=generated_answer.token_estimate,
        )

        self.audit_service.record_llm_call(
            request_id=request_id,
            purpose="answer_generation",
            model_name=generated_answer.model_name,
            input_token_estimate=estimate_tokens(question),
            output_token_estimate=estimate_tokens(generated_answer.answer),
            latency_ms=latency_ms,
            status="success",
        )

        return request_id, generated_answer, chunks, latency_ms