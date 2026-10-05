from uuid import UUID

from app.api.deps import SessionLocal
from app.schemas.evaluations import EvaluationQuestion
from app.services.async_job_service import AsyncJobService
from app.services.evaluation_service import EvaluationService


def run_evaluation_job(job_id: UUID) -> None:
    db = SessionLocal()

    try:
        job_service = AsyncJobService(db)
        evaluation_service = EvaluationService(db)

        job = job_service.mark_running(job_id)
        payload = job.input_payload or {}

        raw_questions = payload.get("questions", [])
        questions = [
            EvaluationQuestion.model_validate(question)
            for question in raw_questions
        ]

        job_service.update_progress(
            job_id=job_id,
            progress_current=0,
            progress_total=len(questions),
        )

        run = evaluation_service.run_evaluation(
            run_name=payload["run_name"],
            questions=questions,
            retrieval_mode=payload.get("retrieval_mode", "hybrid"),
            top_k=payload.get("top_k", 5),
            answer_strategy=payload.get("answer_strategy", "single"),
            answer_provider=payload.get("answer_provider"),
            answer_providers=payload.get("answer_providers"),
        )

        job_service.mark_completed(
            job_id=job_id,
            result_payload={
                "run_id": str(run.id),
                "run_name": run.run_name,
                "average_score": run.average_score,
                "status": run.status,
                "total_questions": run.total_questions,
                "result_endpoint": f"/evaluations/runs/{run.id}",
                "report_endpoint": f"/evaluations/runs/{run.id}/report",
            },
        )

    except Exception as exc:
        db.rollback()
        AsyncJobService(db).mark_failed(
            job_id=job_id,
            error_message=str(exc),
        )
    finally:
        db.close()
