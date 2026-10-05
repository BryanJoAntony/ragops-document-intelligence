from typing import Any

from pydantic import BaseModel


class DashboardMetricResponse(BaseModel):
    name: str
    value: int | float | str | None


class DashboardOverviewResponse(BaseModel):
    documents_total: int
    documents_indexed: int
    chunks_total: int
    query_audits_total: int
    llm_call_logs_total: int
    evaluation_runs_total: int
    citation_validation_results_total: int
    async_jobs_total: int
    latest_activity: list[dict[str, Any]]


class DashboardEvaluationsResponse(BaseModel):
    evaluation_runs_total: int
    completed_runs_total: int
    latest_average_score: float | None
    best_average_score: float | None
    average_of_average_scores: float | None
    citation_validation_results_total: int
    average_citation_validation_score: float | None
    recent_runs: list[dict[str, Any]]


class DashboardRetrievalResponse(BaseModel):
    query_audits_total: int
    retrieval_mode_counts: dict[str, int]
    filter_usage_counts: dict[str, int]
    filtered_query_count: int
    provider_call_counts: dict[str, int]
    average_latency_ms: float | None
    recent_queries: list[dict[str, Any]]


class DashboardJobsResponse(BaseModel):
    async_jobs_total: int
    job_status_counts: dict[str, int]
    job_type_counts: dict[str, int]
    recent_jobs: list[dict[str, Any]]

