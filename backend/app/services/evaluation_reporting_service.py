from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EvaluationResult, EvaluationRun


class EvaluationReportingService:
    def __init__(self, db: Session):
        self.db = db

    def get_run_report(self, run_id: UUID) -> dict | None:
        run = self.db.get(EvaluationRun, run_id)

        if run is None:
            return None

        results = self._get_results(run.id)
        summary = self._summarize_run(run, results)

        return {
            "run": summary,
            "per_question": [
                self._summarize_result(result)
                for result in results
            ],
        }

    def compare_runs(self, run_ids: list[UUID]) -> dict:
        if len(run_ids) < 2:
            raise ValueError("At least two run_ids are required for comparison.")

        runs = [
            self.db.get(EvaluationRun, run_id)
            for run_id in run_ids
        ]

        missing_ids = [
            str(run_id)
            for run_id, run in zip(run_ids, runs)
            if run is None
        ]

        if missing_ids:
            raise ValueError(f"Evaluation run(s) not found: {', '.join(missing_ids)}")

        run_summaries = []

        for run in runs:
            results = self._get_results(run.id)
            run_summaries.append(self._summarize_run(run, results))

        baseline = run_summaries[0]
        comparisons = [
            self._compare_to_baseline(
                baseline=baseline,
                candidate=summary,
            )
            for summary in run_summaries[1:]
        ]

        return {
            "baseline_run_id": baseline["run_id"],
            "run_count": len(run_summaries),
            "runs": run_summaries,
            "comparisons": comparisons,
        }

    def _get_results(self, run_id: UUID) -> list[EvaluationResult]:
        return (
            self.db.query(EvaluationResult)
            .filter(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.created_at.asc())
            .all()
        )

    def _summarize_run(
        self,
        run: EvaluationRun,
        results: list[EvaluationResult],
    ) -> dict:
        scores = [result.score for result in results]
        citation_scores = []
        expected_overlap_scores = []
        latencies = []
        supported_claims = 0
        unsupported_claims = 0

        for result in results:
            details = result.evaluation_details or {}
            score_parts = details.get("score_parts", {})
            citation_validation = details.get("citation_validation", {})

            citation_score = citation_validation.get("validation_score")
            if citation_score is not None:
                citation_scores.append(float(citation_score))

            expected_overlap = score_parts.get("expected_answer_keyword_overlap")
            if expected_overlap is not None:
                expected_overlap_scores.append(float(expected_overlap))

            latency_ms = details.get("latency_ms")
            if latency_ms is not None:
                latencies.append(float(latency_ms))

            supported_claims += int(citation_validation.get("supported_claims_count", 0) or 0)
            unsupported_claims += int(citation_validation.get("unsupported_claims_count", 0) or 0)

        return {
            "run_id": str(run.id),
            "run_name": run.run_name,
            "run_source": (run.run_metadata or {}).get("run_source"),
            "dataset_id": (run.run_metadata or {}).get("dataset_id"),
            "dataset_name": (run.run_metadata or {}).get("dataset_name"),
            "retrieval_mode": run.retrieval_mode,
            "answer_strategy": run.answer_strategy,
            "answer_provider": run.answer_provider,
            "answer_providers": run.answer_providers,
            "status": run.status,
            "total_questions": run.total_questions,
            "result_count": len(results),
            "average_score": run.average_score,
            "computed_average_score": self._safe_average(scores),
            "average_citation_validation_score": self._safe_average(citation_scores),
            "average_expected_answer_overlap": self._safe_average(expected_overlap_scores),
            "average_latency_ms": self._safe_average(latencies),
            "supported_claims_count": supported_claims,
            "unsupported_claims_count": unsupported_claims,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }

    def _summarize_result(self, result: EvaluationResult) -> dict:
        details = result.evaluation_details or {}
        score_parts = details.get("score_parts", {})
        citation_validation = details.get("citation_validation", {})

        return {
            "question": result.question,
            "expected_answer": result.expected_answer,
            "request_id": result.request_id,
            "score": result.score,
            "retrieved_chunks_count": result.retrieved_chunks_count,
            "citations_count": result.citations_count,
            "expected_answer_keyword_overlap": score_parts.get("expected_answer_keyword_overlap"),
            "citation_validation_score": citation_validation.get("validation_score"),
            "supported_claims_count": citation_validation.get("supported_claims_count"),
            "unsupported_claims_count": citation_validation.get("unsupported_claims_count"),
            "latency_ms": details.get("latency_ms"),
            "answer_provider": details.get("answer_provider"),
            "answer_strategy": details.get("answer_strategy"),
        }

    @staticmethod
    def _compare_to_baseline(
        baseline: dict,
        candidate: dict,
    ) -> dict:
        return {
            "baseline_run_id": baseline["run_id"],
            "candidate_run_id": candidate["run_id"],
            "candidate_run_name": candidate["run_name"],
            "average_score_delta": EvaluationReportingService._delta(
                candidate.get("average_score"),
                baseline.get("average_score"),
            ),
            "citation_validation_score_delta": EvaluationReportingService._delta(
                candidate.get("average_citation_validation_score"),
                baseline.get("average_citation_validation_score"),
            ),
            "expected_overlap_delta": EvaluationReportingService._delta(
                candidate.get("average_expected_answer_overlap"),
                baseline.get("average_expected_answer_overlap"),
            ),
            "latency_ms_delta": EvaluationReportingService._delta(
                candidate.get("average_latency_ms"),
                baseline.get("average_latency_ms"),
            ),
        }

    @staticmethod
    def _safe_average(values: list[float]) -> float | None:
        if not values:
            return None

        return round(sum(values) / len(values), 4)

    @staticmethod
    def _delta(candidate_value, baseline_value) -> float | None:
        if candidate_value is None or baseline_value is None:
            return None

        return round(float(candidate_value) - float(baseline_value), 4)
