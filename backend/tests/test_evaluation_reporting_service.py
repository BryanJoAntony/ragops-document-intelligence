from datetime import datetime, timezone
from uuid import uuid4

from app.services.evaluation_reporting_service import EvaluationReportingService


class FakeRun:
    def __init__(self):
        self.id = uuid4()
        self.run_name = "fake_run"
        self.run_metadata = {
            "run_source": "evaluation_dataset",
            "dataset_id": str(uuid4()),
            "dataset_name": "core_storage_benchmark_v1",
        }
        self.retrieval_mode = "hybrid"
        self.answer_strategy = "compare"
        self.answer_provider = None
        self.answer_providers = ["local_extractive", "local_summary"]
        self.status = "completed"
        self.total_questions = 2
        self.average_score = 0.9
        self.created_at = datetime.now(timezone.utc)


class FakeResult:
    def __init__(self, score: float, overlap: float, citation_score: float, latency_ms: int):
        self.question = "Where should audit history be stored?"
        self.expected_answer = "Audit history should be stored in PostgreSQL."
        self.request_id = f"req_{uuid4().hex}"
        self.score = score
        self.retrieved_chunks_count = 1
        self.citations_count = 1
        self.created_at = datetime.now(timezone.utc)
        self.evaluation_details = {
            "latency_ms": latency_ms,
            "answer_provider": "local_extractive",
            "answer_strategy": "compare",
            "score_parts": {
                "expected_answer_keyword_overlap": overlap,
            },
            "citation_validation": {
                "validation_score": citation_score,
                "supported_claims_count": 1,
                "unsupported_claims_count": 0,
            },
        }


def test_safe_average_returns_none_for_empty_list() -> None:
    assert EvaluationReportingService._safe_average([]) is None


def test_safe_average_rounds_values() -> None:
    assert EvaluationReportingService._safe_average([0.9, 0.95]) == 0.925


def test_delta_returns_difference() -> None:
    assert EvaluationReportingService._delta(0.95, 0.90) == 0.05


def test_delta_returns_none_when_missing() -> None:
    assert EvaluationReportingService._delta(None, 0.90) is None


def test_summarize_run_calculates_report_metrics() -> None:
    service = EvaluationReportingService.__new__(EvaluationReportingService)
    run = FakeRun()
    results = [
        FakeResult(score=0.9, overlap=0.75, citation_score=1.0, latency_ms=100),
        FakeResult(score=0.8, overlap=0.50, citation_score=0.75, latency_ms=200),
    ]

    summary = service._summarize_run(run, results)

    assert summary["run_name"] == "fake_run"
    assert summary["run_source"] == "evaluation_dataset"
    assert summary["dataset_name"] == "core_storage_benchmark_v1"
    assert summary["computed_average_score"] == 0.85
    assert summary["average_citation_validation_score"] == 0.875
    assert summary["average_expected_answer_overlap"] == 0.625
    assert summary["average_latency_ms"] == 150.0
    assert summary["supported_claims_count"] == 2
    assert summary["unsupported_claims_count"] == 0


def test_compare_to_baseline_calculates_deltas() -> None:
    baseline = {
        "run_id": "baseline",
        "average_score": 0.8,
        "average_citation_validation_score": 0.75,
        "average_expected_answer_overlap": 0.5,
        "average_latency_ms": 200,
    }
    candidate = {
        "run_id": "candidate",
        "run_name": "candidate_run",
        "average_score": 0.9,
        "average_citation_validation_score": 1.0,
        "average_expected_answer_overlap": 0.75,
        "average_latency_ms": 150,
    }

    comparison = EvaluationReportingService._compare_to_baseline(
        baseline=baseline,
        candidate=candidate,
    )

    assert comparison["average_score_delta"] == 0.1
    assert comparison["citation_validation_score_delta"] == 0.25
    assert comparison["expected_overlap_delta"] == 0.25
    assert comparison["latency_ms_delta"] == -50.0
