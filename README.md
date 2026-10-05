# RAGOps Document Intelligence

RAG/document-intelligence backend for making document answers retrievable, cited, evaluated, audited, and observable.

This project shows how uploaded documents can move through a complete RAGOps-style workflow: ingestion, parsing, chunking, indexing, retrieval, cited answer generation, evaluation, citation validation, async job tracking, dashboard metrics, and cost-aware routing plans.

The backend is built with FastAPI, PostgreSQL, Qdrant, Redis, and Docker Compose. A minimal React dashboard is included for local inspection and demo use.

## What this project includes

- Document upload and ingestion
- Document parsing and chunking
- File hashing and duplicate handling
- PostgreSQL-backed document, chunk, audit, evaluation, citation-validation, and async-job storage
- Qdrant vector indexing
- Redis service integration
- Vector retrieval
- BM25 retrieval
- Fuzzy retrieval
- Hybrid retrieval
- Metadata-aware retrieval filters
- Cited answer generation
- Local deterministic answer providers
- Optional OpenAI answer provider
- Single-provider and compare-mode answer orchestration
- Query audit logging
- Provider call logging
- Citation validation
- Evaluation runs
- Reusable evaluation datasets
- Benchmark run reporting
- Evaluation run comparison
- Async evaluation jobs
- Dashboard metrics APIs
- Model routing and cost planning
- Minimal React dashboard frontend

## Current status

This is a local portfolio project built in milestones.

The backend runs locally through Docker Compose. The frontend is a lightweight local dashboard for inspecting the backend. The project is not presented as a fully deployed enterprise product.

## Tech stack

### Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Qdrant
- Redis
- Docker Compose
- pytest

### Retrieval and RAG

- Vector retrieval
- BM25 retrieval
- Fuzzy matching
- Hybrid retrieval
- Metadata filters
- Cited answer generation
- Citation validation
- Deterministic evaluation scoring

### Frontend

- React
- Vite
- TypeScript
- CSS
- lucide-react

## Architecture

High-level flow:

~~~text
Document Upload
      ↓
Storage + Metadata
      ↓
Parsing
      ↓
Chunking
      ↓
Embeddings
      ↓
Qdrant Vector Index
      ↓
Retrieval: vector / BM25 / fuzzy / hybrid
      ↓
Answer Provider: local_extractive / local_summary / optional OpenAI
      ↓
Cited Answer
      ↓
Audit Logs + Provider Logs
      ↓
Evaluation + Citation Validation
      ↓
Dashboard Metrics
~~~

Core service flow:

~~~text
FastAPI routes
    ↓
Service layer
    ↓
PostgreSQL / Qdrant / Redis
~~~

PostgreSQL is the durable source of truth for application data. Qdrant stores vector search data. Redis is included as supporting runtime/cache infrastructure.

## Main API areas

### Health

~~~text
GET /health
GET /health/deps
~~~

### Documents

~~~text
POST /documents/upload
POST /documents/{document_id}/parse
POST /documents/{document_id}/index
GET /documents
GET /documents/{document_id}
~~~

### Query / RAG

~~~text
POST /query/ask
GET /query/audits/{request_id}
~~~

### Citation validation

~~~text
POST /citations/validate-rag
~~~

### Evaluations

~~~text
POST /evaluations/run
GET /evaluations/runs/{run_id}
GET /evaluations/runs/{run_id}/report
GET /evaluations/runs/compare
POST /evaluations/datasets
GET /evaluations/datasets
GET /evaluations/datasets/{dataset_id}
POST /evaluations/datasets/{dataset_id}/run
~~~

### Async jobs

~~~text
POST /jobs/evaluations/run
GET /jobs/{job_id}
~~~

### Dashboard

~~~text
GET /dashboard/overview
GET /dashboard/evaluations
GET /dashboard/retrieval
GET /dashboard/jobs
~~~

### Routing

~~~text
POST /routing/answer-plan
~~~

## Example query request

~~~json
{
  "question": "Where should audit history be stored?",
  "top_k": 5,
  "retrieval_mode": "hybrid",
  "filters": {
    "filename": "sample_policy_milestone3.txt"
  },
  "answer_strategy": "single",
  "answer_provider": "local_extractive"
}
~~~

## Example routing request

~~~json
{
  "question": "Where should audit history be stored?",
  "retrieval_mode": "hybrid",
  "top_k": 5,
  "task_type": "qa",
  "priority": "cost",
  "allow_paid_providers": false,
  "max_estimated_cost_usd": 0.0
}
~~~

## Running locally

Start backend services:

~~~powershell
docker compose up -d --build
~~~

Apply migrations:

~~~powershell
docker compose exec api alembic upgrade head
~~~

Run backend tests:

~~~powershell
docker compose exec api pytest -q
~~~

Backend URL:

~~~text
http://localhost:8000
~~~

API docs:

~~~text
http://localhost:8000/docs
~~~

## Running the frontend

Use Node.js 22 or later.

From the frontend folder:

~~~powershell
cd frontend
npm.cmd install
npm.cmd run dev
~~~

Frontend URL:

~~~text
http://localhost:5173
~~~

Production build:

~~~powershell
npm.cmd run build
~~~

## Dashboard frontend

The minimal dashboard includes:

- Overview
- Retrieval
- Evaluations
- Jobs
- Routing
- Ask Demo

The frontend is intentionally lightweight. It is a local observability and demo layer over the backend APIs.

## Evaluation and citation validation

The project includes deterministic evaluation foundations for checking:

- whether an answer exists
- whether citations exist
- whether retrieved context exists
- expected-answer keyword overlap
- citation-validation score

Citation validation checks cited answer markers against returned citations and retrieved chunks. Validation results are persisted for later inspection.

This is not presented as full semantic entailment verification or an LLM-judge system.

## Model routing and cost planning

The routing endpoint recommends an answer provider or strategy based on:

- task type
- priority
- paid-provider permission
- estimated context tokens
- estimated output tokens
- estimated cost
- provider availability

This is a transparent planning layer. It does not automatically execute fallback or hidden provider switching.

## Async job processing

The async job foundation supports background evaluation runs with persisted job status.

Supported job states:

- queued
- running
- completed
- failed

The current implementation uses FastAPI BackgroundTasks. It is suitable as a local async foundation, not a full distributed worker queue.

## Implementation summary

The project was built across focused milestones covering:

- Docker and service foundation
- PostgreSQL schema and Alembic migrations
- Document upload, storage, parsing, and chunking
- Embedding generation and Qdrant indexing
- Cited RAG answers and audit logging
- Vector, BM25, fuzzy, and hybrid retrieval
- Configurable answer providers
- Answer orchestration and compare mode
- Evaluation framework
- Citation validation
- Evaluation datasets and repeatable benchmark runs
- Evaluation reporting and run comparison
- Async evaluation jobs
- Metadata-aware retrieval
- Dashboard backend metrics
- Model routing and cost planning
- Query-audit retrieval metadata
- Minimal React dashboard frontend
- Final documentation and portfolio packaging

## Known limitations

- Local portfolio/demo project, not a deployed enterprise system.
- No authentication or authorization yet.
- No tenant-level access-control enforcement yet.
- No production secrets-management setup.
- No production frontend container yet.
- No durable distributed worker queue yet.
- No automatic model fallback execution.
- No LLM judge/combiner layer.
- No frontend tests yet.
- No advanced dashboard charts yet.
- Existing older audit rows may not contain retrieval metadata.
- OpenAI provider is optional and depends on configuration.

## Portfolio description

RAGOps Document Intelligence is a production-style personal RAG backend built with FastAPI, PostgreSQL, Qdrant, Redis, and Docker Compose. It supports document ingestion, parsing, chunking, hybrid retrieval, cited answer generation, citation validation, evaluation datasets, benchmark reporting, async evaluation jobs, dashboard metrics, cost-aware routing plans, and a minimal React dashboard frontend.

## Positioning

This project is best described as:

~~~text
RAG backend + document intelligence + evaluation + observability
~~~

It is focused on RAG/document intelligence and traceability. Agentic workflows, tool orchestration, and MCP-style work are intentionally kept separate for a different project.
