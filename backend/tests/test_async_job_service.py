from uuid import uuid4

from app.schemas.jobs import AsyncEvaluationRunRequest
from app.services.async_job_service import AsyncJobService


def test_async_evaluation_request_inherits_evaluation_request() -> None:
    request = AsyncEvaluationRunRequest(
        run_name="async_eval_smoke_test",
        retrieval_mode="hybrid",
        top_k=5,
        answer_strategy="compare",
        answer_providers=["local_extractive", "local_summary"],
        questions=[
            {
                "question": "Where should audit history be stored?",
                "expected_answer": "Audit history should be stored in PostgreSQL.",
            }
        ],
    )

    assert request.run_name == "async_eval_smoke_test"
    assert request.questions[0].question == "Where should audit history be stored?"
    assert request.answer_strategy == "compare"


def test_async_job_mark_completed_sets_status() -> None:
    class FakeJob:
        def __init__(self):
            self.id = uuid4()
            self.status = "running"
            self.result_payload = {}
            self.error_message = "old error"
            self.progress_current = 0
            self.progress_total = 1
            self.completed_at = None

    class FakeDb:
        def __init__(self):
            self.job = FakeJob()

        def get(self, model, job_id):
            return self.job

        def commit(self):
            pass

        def refresh(self, job):
            pass

    db = FakeDb()
    service = AsyncJobService(db)

    job = service.mark_completed(
        job_id=db.job.id,
        result_payload={"run_id": "run_123"},
    )

    assert job.status == "completed"
    assert job.result_payload == {"run_id": "run_123"}
    assert job.error_message is None
    assert job.progress_current == 1
    assert job.completed_at is not None


def test_async_job_mark_failed_sets_error() -> None:
    class FakeJob:
        def __init__(self):
            self.id = uuid4()
            self.status = "running"
            self.error_message = None
            self.completed_at = None

    class FakeDb:
        def __init__(self):
            self.job = FakeJob()

        def get(self, model, job_id):
            return self.job

        def commit(self):
            pass

        def refresh(self, job):
            pass

    db = FakeDb()
    service = AsyncJobService(db)

    job = service.mark_failed(
        job_id=db.job.id,
        error_message="boom",
    )

    assert job.status == "failed"
    assert job.error_message == "boom"
    assert job.completed_at is not None


def test_async_job_requires_existing_job() -> None:
    class FakeDb:
        def get(self, model, job_id):
            return None

    service = AsyncJobService(FakeDb())

    try:
        service._require_job(uuid4())
    except ValueError as exc:
        assert "Async job not found" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing async job")
