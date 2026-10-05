from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    AsyncJob,
    CitationValidationResult,
    Document,
    DocumentChunk,
    EvaluationRun,
    LLMCallLog,
    QueryAudit,
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self) -> dict:
        latest_activity = []

        recent_queries = (
            self.db.query(QueryAudit)
            .order_by(QueryAudit.created_at.desc())
            .limit(3)
            .all()
        )

        for query in recent_queries:
            latest_activity.append(
                {
                    "type": "query",
                    "id": query.request_id,
                    "label": query.query_text,
                    "created_at": query.created_at.isoformat() if query.created_at else None,
                }
            )

        recent_runs = (
            self.db.query(EvaluationRun)
            .order_by(EvaluationRun.created_at.desc())
            .limit(3)
            .all()
        )

        for run in recent_runs:
            latest_activity.append(
                {
                    "type": "evaluation_run",
                    "id": str(run.id),
                    "label": run.run_name,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                }
            )

        recent_jobs = (
            self.db.query(AsyncJob)
            .order_by(AsyncJob.created_at.desc())
            .limit(3)
            .all()
        )

        for job in recent_jobs:
            latest_activity.append(
                {
                    "type": "async_job",
                    "id": str(job.id),
                    "label": f"{job.job_type}:{job.status}",
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                }
            )

        latest_activity.sort(
            key=lambda item: item.get("created_at") or "",
            reverse=True,
        )

        return {
            "documents_total": self._count(Document),
            "documents_indexed": (
                self.db.query(Document)
                .filter(Document.status == "indexed")
                .count()
            ),
            "chunks_total": self._count(DocumentChunk),
            "query_audits_total": self._count(QueryAudit),
            "llm_call_logs_total": self._count(LLMCallLog),
            "evaluation_runs_total": self._count(EvaluationRun),
            "citation_validation_results_total": self._count(CitationValidationResult),
            "async_jobs_total": self._count(AsyncJob),
            "latest_activity": latest_activity[:10],
        }

    def get_evaluations(self) -> dict:
        completed_runs = (
            self.db.query(EvaluationRun)
            .filter(EvaluationRun.status == "completed")
            .order_by(EvaluationRun.created_at.desc())
            .all()
        )

        average_scores = [
            float(run.average_score)
            for run in completed_runs
            if run.average_score is not None
        ]

        recent_runs = completed_runs[:10]

        citation_scores = [
            float(row[0])
            for row in (
                self.db.query(CitationValidationResult.validation_score)
                .filter(CitationValidationResult.validation_score.isnot(None))
                .all()
            )
        ]

        return {
            "evaluation_runs_total": self._count(EvaluationRun),
            "completed_runs_total": len(completed_runs),
            "latest_average_score": average_scores[0] if average_scores else None,
            "best_average_score": max(average_scores) if average_scores else None,
            "average_of_average_scores": self._average(average_scores),
            "citation_validation_results_total": self._count(CitationValidationResult),
            "average_citation_validation_score": self._average(citation_scores),
            "recent_runs": [
                {
                    "run_id": str(run.id),
                    "run_name": run.run_name,
                    "status": run.status,
                    "average_score": run.average_score,
                    "retrieval_mode": run.retrieval_mode,
                    "answer_strategy": run.answer_strategy,
                    "run_source": (run.run_metadata or {}).get("run_source"),
                    "dataset_name": (run.run_metadata or {}).get("dataset_name"),
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                }
                for run in recent_runs
            ],
        }

    def get_retrieval(self) -> dict:
        recent_queries = (
            self.db.query(QueryAudit)
            .order_by(QueryAudit.created_at.desc())
            .limit(10)
            .all()
        )

        provider_counts = self._group_count(LLMCallLog.model_name)

        latencies = [
            float(row[0])
            for row in (
                self.db.query(QueryAudit.latency_ms)
                .filter(QueryAudit.latency_ms.isnot(None))
                .all()
            )
        ]

        retrieval_mode_counts = self._group_count(QueryAudit.retrieval_mode)
        filter_usage_counts = self._build_filter_usage_counts()

        return {
            "query_audits_total": self._count(QueryAudit),
            "retrieval_mode_counts": retrieval_mode_counts,
            "filter_usage_counts": filter_usage_counts,
            "filtered_query_count": sum(filter_usage_counts.values()),
            "provider_call_counts": provider_counts,
            "average_latency_ms": self._average(latencies),
            "recent_queries": [
                {
                    "request_id": query.request_id,
                    "query_text": query.query_text,
                    "retrieval_top_k": query.retrieval_top_k,
                    "retrieval_mode": query.retrieval_mode,
                    "query_filters": query.query_filters or {},
                    "retrieved_chunk_count": len(query.retrieved_chunk_ids or []),
                    "model_name": query.model_name,
                    "latency_ms": query.latency_ms,
                    "created_at": query.created_at.isoformat() if query.created_at else None,
                }
                for query in recent_queries
            ],
        }

    def get_jobs(self) -> dict:
        recent_jobs = (
            self.db.query(AsyncJob)
            .order_by(AsyncJob.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "async_jobs_total": self._count(AsyncJob),
            "job_status_counts": self._group_count(AsyncJob.status),
            "job_type_counts": self._group_count(AsyncJob.job_type),
            "recent_jobs": [
                {
                    "job_id": str(job.id),
                    "job_type": job.job_type,
                    "status": job.status,
                    "progress_current": job.progress_current,
                    "progress_total": job.progress_total,
                    "error_message": job.error_message,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                }
                for job in recent_jobs
            ],
        }

    def _count(self, model) -> int:
        return self.db.query(model).count()

    def _group_count(self, column) -> dict[str, int]:
        rows = (
            self.db.query(column, func.count())
            .group_by(column)
            .all()
        )

        return {
            str(key) if key is not None else "unknown": int(count)
            for key, count in rows
        }

    def _build_filter_usage_counts(self) -> dict[str, int]:
        rows = (
            self.db.query(QueryAudit.query_filters)
            .filter(QueryAudit.query_filters.isnot(None))
            .all()
        )

        counts: dict[str, int] = {}

        for row in rows:
            filters = row[0] or {}

            if not filters:
                continue

            for key, value in filters.items():
                if value is None:
                    continue

                counts[key] = counts.get(key, 0) + 1

        return counts

    @staticmethod
    def _average(values: list[float]) -> float | None:
        if not values:
            return None

        return round(sum(values) / len(values), 4)
