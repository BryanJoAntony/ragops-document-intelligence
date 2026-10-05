# Portfolio Notes

## One-line description

RAGOps Document Intelligence is a production-style RAG backend for document ingestion, hybrid retrieval, cited answer generation, citation validation, evaluation, benchmark reporting, async jobs, dashboard metrics, and cost-aware model routing.

## Resume version

Built a production-style RAG/document-intelligence backend using FastAPI, PostgreSQL, Qdrant, Redis, and Docker Compose, supporting document ingestion, hybrid retrieval, cited answers, citation validation, evaluation datasets, benchmark reporting, async evaluation jobs, dashboard metrics, and cost-aware answer-provider routing.

## Stronger resume version

Built a RAGOps-focused document intelligence backend with FastAPI, PostgreSQL, Qdrant, Redis, and Docker Compose, implementing document ingestion, chunking, vector/BM25/fuzzy/hybrid retrieval, cited answer generation, citation validation, repeatable evaluation benchmarks, async evaluation jobs, dashboard metrics, and model cost-planning APIs.

## Interview explanation

I built this as a RAGOps-focused backend project. The goal was not only to generate answers from documents, but to make the process auditable and measurable.

The system supports uploading and parsing documents, chunking them, indexing embeddings in Qdrant, and retrieving context through vector, BM25, fuzzy, or hybrid retrieval. Answers include citations back to retrieved chunks.

After the core RAG flow, I added evaluation datasets, repeatable benchmark runs, citation validation, run reports, run comparison, async evaluation jobs, dashboard metrics, model routing/cost planning, and a minimal React dashboard frontend.

I kept local deterministic answer providers so the project can run and be tested without paid API access, while also allowing optional OpenAI provider integration.

## What it proves

- Python backend development
- FastAPI service design
- PostgreSQL schema and migration work
- SQLAlchemy/Alembic usage
- RAG pipeline design
- Hybrid retrieval
- Vector search with Qdrant
- BM25 and fuzzy retrieval
- Citation traceability
- Evaluation workflow design
- API observability
- Async job tracking
- Cost-aware model routing
- React dashboard basics
- Docker Compose development workflow

## Honest limitations

- Local portfolio project, not fully deployed.
- No authentication/authorization yet.
- No production worker queue yet.
- No tenant-level access-control enforcement yet.
- No LLM judge/combiner yet.
- No automatic model fallback execution yet.
- No frontend tests yet.
- No advanced dashboard charts yet.
- OpenAI provider is optional and depends on configuration.

## How to describe it in applications

Use this:

RAGOps Document Intelligence is a production-style personal backend project I built to make document-based RAG answers more traceable and measurable. It includes document ingestion, parsing, chunking, hybrid retrieval, cited answer generation, citation validation, evaluation datasets, benchmark reporting, async evaluation jobs, dashboard metrics, cost-aware routing plans, and a minimal React dashboard frontend.

Avoid saying:

- Fully deployed enterprise system
- Production customer platform
- Autonomous agent system
- LLM judge framework
- Complete MLOps platform
- Production Kubernetes deployment

## Separation from next project

This project should stay focused on RAG/document intelligence.

Agentic workflows, tool orchestration, MCP-style tools, planner/executor flows, and multi-agent decision logic should be handled in a separate project.

## LinkedIn post angle

Making a RAG project easier to inspect instead of only showing API responses.

## Possible LinkedIn question

For RAG projects, what is more useful to show in a portfolio: the retrieval pipeline itself, evaluation metrics, citation validation, or a small dashboard UI?

## Keywords

RAGOps, RAG, Document Intelligence, FastAPI, Python, PostgreSQL, Qdrant, Redis, Docker Compose, Hybrid Retrieval, Citation Validation, RAG Evaluation, LLMOps, Backend Engineering, AI Engineering, React, Vite, TypeScript
