from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AsyncJob


class AsyncJobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        job_type: str,
        input_payload: dict,
        progress_total: int = 0,
    ) -> AsyncJob:
        job = AsyncJob(
            job_type=job_type,
            status="queued",
            input_payload=input_payload,
            result_payload={},
            progress_current=0,
            progress_total=progress_total,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    def get_job(self, job_id: UUID) -> AsyncJob | None:
        return self.db.get(AsyncJob, job_id)

    def mark_running(self, job_id: UUID) -> AsyncJob:
        job = self._require_job(job_id)
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_progress(
        self,
        job_id: UUID,
        progress_current: int,
        progress_total: int | None = None,
    ) -> AsyncJob:
        job = self._require_job(job_id)
        job.progress_current = progress_current

        if progress_total is not None:
            job.progress_total = progress_total

        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed(
        self,
        job_id: UUID,
        result_payload: dict,
    ) -> AsyncJob:
        job = self._require_job(job_id)
        job.status = "completed"
        job.result_payload = result_payload
        job.error_message = None
        job.progress_current = job.progress_total
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_failed(
        self,
        job_id: UUID,
        error_message: str,
    ) -> AsyncJob:
        job = self._require_job(job_id)
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def _require_job(self, job_id: UUID) -> AsyncJob:
        job = self.get_job(job_id)

        if job is None:
            raise ValueError(f"Async job not found: {job_id}")

        return job
