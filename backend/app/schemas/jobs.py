from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.schemas.evaluations import EvaluationRunRequest


class AsyncEvaluationRunRequest(EvaluationRunRequest):
    pass


class AsyncJobSubmitResponse(BaseModel):
    job_id: UUID
    job_type: str
    status: str
    message: str


class AsyncJobResponse(BaseModel):
    job_id: UUID
    job_type: str
    status: str
    input_payload: dict[str, Any]
    result_payload: dict[str, Any]
    error_message: str | None
    progress_current: int
    progress_total: int
    created_at: Any
    started_at: Any
    completed_at: Any
    updated_at: Any
