# Architecture

## Purpose

RAGOps Document Intelligence is a RAG/document-intelligence backend focused on making document answers traceable, cited, evaluated, and observable.

The project is not designed as an agentic workflow system. It focuses on RAG infrastructure and RAGOps-style inspection.

## Main components

~~~text
FastAPI API
PostgreSQL
Qdrant
Redis
React dashboard frontend
~~~

## Data responsibilities

### PostgreSQL

PostgreSQL stores durable application data:

- documents
- document chunks
- query audits
- provider call logs
- evaluation datasets
- evaluation runs
- evaluation results
- citation validation results
- async jobs

### Qdrant

Qdrant stores vector-indexed chunk embeddings and payload metadata used for vector search.

### Redis

Redis is included as runtime/cache infrastructure. It is not the durable source of truth.

### Frontend

The frontend is a minimal React/Vite dashboard. It calls backend APIs and displays dashboard, retrieval, evaluation, job, routing, and ask-demo views.

## Query flow

~~~text
POST /query/ask
      ↓
RagQueryService
      ↓
RetrievalService
      ↓
vector / BM25 / fuzzy / hybrid retrieval
      ↓
AnswerOrchestrationService
      ↓
answer provider
      ↓
cited answer
      ↓
AuditService
      ↓
query_audits + llm_call_logs
~~~

## Evaluation flow

~~~text
POST /evaluations/run
      ↓
EvaluationService
      ↓
RagQueryService
      ↓
answer + citations
      ↓
CitationValidationService
      ↓
evaluation_results + citation_validation_results
~~~

## Dataset benchmark flow

~~~text
POST /evaluations/datasets/{dataset_id}/run
      ↓
EvaluationDatasetService
      ↓
EvaluationService
      ↓
stored benchmark results
      ↓
report / comparison endpoints
~~~

## Async evaluation flow

~~~text
POST /jobs/evaluations/run
      ↓
async_jobs row created
      ↓
FastAPI BackgroundTasks
      ↓
EvaluationService
      ↓
job status/result updated
~~~

## Dashboard flow

~~~text
GET /dashboard/*
      ↓
DashboardService
      ↓
read existing PostgreSQL tables
      ↓
dashboard-ready metrics
~~~

## Routing flow

~~~text
POST /routing/answer-plan
      ↓
ModelRoutingService
      ↓
estimate context/output tokens
      ↓
estimate provider costs
      ↓
recommend provider or compare strategy
~~~

## Design choices

- Keep routes thin.
- Put business logic in services.
- Use PostgreSQL for durable audit and evaluation data.
- Use Qdrant for vector retrieval.
- Keep local deterministic providers available so tests do not require paid API access.
- Keep routing as a transparent planning layer before adding automatic fallback.
- Keep the frontend as a thin demo/observability layer.
- Keep agentic workflows out of this project so the scope stays focused on RAG/document intelligence.

## Current limitations

- No authentication/authorization yet.
- No tenant access-control enforcement yet.
- No production worker queue yet.
- No automatic model fallback execution.
- No LLM judge/combiner.
- No production frontend container yet.
- No frontend tests yet.
