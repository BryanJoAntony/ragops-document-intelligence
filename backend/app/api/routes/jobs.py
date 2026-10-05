from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.jobs import (
    AsyncEvaluationRunRequest,
    AsyncJobResponse,
    AsyncJobSubmitResponse,
)
from app.services.async_job_runner import run_evaluation_job
from app.services.async_job_service import AsyncJobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/evaluations/run", response_model=AsyncJobSubmitResponse)
def submit_async_evaluation_run(
    request: AsyncEvaluationRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AsyncJobSubmitResponse:
    service = AsyncJobService(db)

    job = service.create_job(
        job_type="evaluation_run",
        input_payload=request.model_dump(mode="json"),
        progress_total=len(request.questions),
    )

    background_tasks.add_task(run_evaluation_job, job.id)

    return AsyncJobSubmitResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        message="Evaluation job queued.",
    )


@router.get("/{job_id}", response_model=AsyncJobResponse)
def get_async_job(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> AsyncJobResponse:
    service = AsyncJobService(db)
    job = service.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Async job not found.")

    return AsyncJobResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        input_payload=job.input_payload,
        result_payload=job.result_payload,
        error_message=job.error_message,
        progress_current=job.progress_current,
        progress_total=job.progress_total,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        updated_at=job.updated_at,
    )
