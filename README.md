# ragops-document-intelligence

A production-style RAGOps/document intelligence platform for ingesting documents, storing metadata, parsing content, chunking with traceability, indexing chunks into a vector database, retrieving relevant context, generating cited answers, tracking audit history, and preparing for RAG quality evaluation.

This project is being built milestone by milestone to demonstrate backend engineering for AI systems, not just a basic chatbot demo.

## Current public milestone

Milestone 3: hybrid retrieval and configurable answer providers.

This public milestone combines the internal hybrid retrieval and configurable answer-provider work into one GitHub milestone after the retrieval and cited answer foundation.

## What this milestone includes

- FastAPI backend
- Docker Compose development setup
- PostgreSQL relational persistence
- Redis runtime/cache layer
- Qdrant vector database service
- SQLAlchemy ORM setup
- Alembic database migrations
- Document upload and local storage
- SHA-256 file hashing and duplicate detection
- TXT, PDF, and DOCX parsing
- Document chunking with metadata
- Sentence-transformer embeddings
- Qdrant vector indexing
- Vector search over document chunks
- BM25 keyword retrieval
- Fuzzy retrieval
- Hybrid retrieval with score merging
- Retrieval score details
- Basic cited RAG answer generation
- Query audit logging in PostgreSQL
- LLM call logging in PostgreSQL
- Configurable answer providers
- Local deterministic answer provider
- Optional OpenAI answer provider
- Token estimate metadata
- Estimated cost metadata
- Clean OpenAI missing-key error handling
- pytest test foundation
- Dependency health checks
- Structured logging foundation

## Why this matters

A RAG system needs more than vector search and an LLM call.

Retrieval quality depends on how chunks are selected, scored, combined, and inspected. This milestone adds multiple retrieval modes and makes provider selection explicit so the system can be tested locally while still supporting external LLM providers later.

The goal is to make retrieval and answer generation easier to debug, audit, and improve.

## Architecture at this milestone

User uploads document
        |
        v
FastAPI upload route
        |
        v
Local storage + SHA-256 duplicate check
        |
        v
PostgreSQL document record
        |
        v
Parser + chunking + metadata tagging
        |
        v
PostgreSQL document_chunks
        |
        v
Embedding service
        |
        v
Qdrant vector index
        |
        v
Retrieval service
        |
        +--> vector retrieval
        +--> BM25 retrieval
        +--> fuzzy retrieval
        +--> hybrid retrieval
        |
        v
Answer generation service
        |
        +--> local_extractive provider
        +--> optional OpenAI provider
        |
        v
Cited answer + PostgreSQL audit logs

## Core services

The project keeps business logic in services instead of putting everything into FastAPI routes.

Current service responsibilities include:

- storage service: handles local file persistence
- document parser service: extracts text from supported file types
- chunking service: splits parsed text into traceable chunks
- metadata tagging service: creates basic generated tags
- ingestion service: coordinates parsing, chunking, metadata, and persistence
- embedding service: creates embeddings for document chunks
- vector store service: manages Qdrant collection and indexing operations
- document indexing service: sends chunk embeddings into Qdrant
- retrieval service: retrieves relevant chunks across vector, BM25, fuzzy, and hybrid modes
- answer generation service: creates cited answers using the selected provider
- audit service: records query and model-call history in PostgreSQL

This structure keeps routes thin and prepares the project for later orchestration, evaluation, dashboards, background jobs, and agent/MCP-style tools.

## Retrieval modes

Current retrieval modes:

- vector: semantic similarity using Qdrant
- BM25: keyword-based retrieval over stored chunks
- fuzzy: approximate text matching over chunk metadata/text
- hybrid: combines vector, BM25, and fuzzy signals into a merged score

Hybrid retrieval returns score details so the retrieved chunks can be inspected instead of treated as a black box.

## Answer providers

Current answer providers:

- local_extractive: deterministic local provider for free, repeatable testing
- openai: optional external provider when an API key is configured

The default provider is local_extractive so the system can be tested without external API calls or token cost.

If OpenAI is selected without an API key, the API returns a clean error instead of silently falling back.

## Database foundation

PostgreSQL is used as the durable source of truth for:

- uploaded documents
- document metadata
- document chunks
- generated tags
- query audits
- LLM call logs
- future evaluation results

Alembic is used for database migrations so schema changes are versioned instead of being manually applied.

## Why PostgreSQL?

PostgreSQL is the default relational database for this project because it is production-friendly, Docker-friendly, widely used in backend and AI systems, and supports structured relational data plus JSONB-style metadata when needed.

In this project:

- PostgreSQL stores durable metadata and audit history.
- Qdrant stores vector embeddings.
- Redis stores temporary runtime/cache state only.

## Why Qdrant?

Qdrant is used as the vector database for document chunk embeddings and similarity search.

PostgreSQL remains the source of truth for document records, chunk metadata, and audit history. Qdrant is used for vector retrieval, not durable business history.

## Why Redis?

Redis is used for temporary runtime data such as:

- cache entries
- rate-limit counters
- job status
- dashboard counters
- temporary runtime state

Durable audit history belongs in PostgreSQL, not Redis.

## Logging and audit strategy

The application logs to:

1. structured stdout/stderr logs for Docker and future centralized log collectors
2. mounted local file logs for debugging
3. PostgreSQL audit tables for durable AI workflow history

Local file logs are written to:

- ./logs/app.log
- ./logs/errors.log

The project avoids logging secrets, sensitive document text, and full prompts by default.

## Current API areas

At this milestone, the important API areas are:

- GET /health
- GET /health/deps
- POST /documents/upload
- GET /documents
- GET /documents/{document_id}
- POST /documents/{document_id}/ingest
- GET /documents/{document_id}/chunks
- POST /documents/{document_id}/index
- POST /documents/{document_id}/search
- POST /query/ask
- GET /query/audits/{request_id}

## Supported document types at this milestone

- .txt
- .pdf
- .docx

## Local development

Start the full stack:

docker compose up --build

Check service health:

curl.exe http://localhost:8000/health/deps

Expected dependencies:

- postgres: ok
- redis: ok
- qdrant: ok

Run tests:

docker compose exec api pytest -q

## Milestone progress

### Public Milestone 0 — Backend foundation

Completed:

- Dockerized FastAPI backend
- PostgreSQL container
- Redis container
- Qdrant container
- Health endpoints
- Dependency health checks
- Structured logging foundation

### Public Milestone 1 — Document ingestion foundation

Completed:

- SQLAlchemy + Alembic schema foundation
- documents table
- document_chunks table
- upload endpoint
- local storage abstraction
- file hashing
- duplicate detection
- parser service
- chunking service
- metadata tagging
- ingestion endpoint
- chunk inspection endpoint

### Public Milestone 2 — Retrieval and cited answer foundation

Completed:

- embedding service
- Qdrant vector collection
- document indexing service
- vector search endpoint
- retrieval service
- conservative local answer generation
- citation markers like [C1]
- query audit logging
- LLM call logging
- pytest foundation

### Public Milestone 3 — Hybrid retrieval and configurable answer providers

Completed:

- vector retrieval mode
- BM25 retrieval mode
- fuzzy retrieval mode
- hybrid retrieval mode
- retrieval score details
- BM25 keyword-overlap fallback for small local corpora
- configurable answer_provider selection
- local_extractive default provider
- optional OpenAI provider
- answer metadata with provider, token estimates, and estimated cost
- clean missing OPENAI_API_KEY error
- no hidden fallback behavior

## Roadmap

Planned next milestones:

- multi-provider orchestration
- model comparison
- retrieval evaluation datasets
- citation validation
- async ingestion jobs
- metadata filtering
- RAGOps dashboard
- agent/MCP-style tool exposure
- deployment hardening
- portfolio documentation polish

## Project goal

The goal is to build a production-style document intelligence platform where users can upload documents, parse and chunk them, index them for retrieval, ask cited questions, inspect retrieval decisions, compare answer providers, evaluate RAG quality, and monitor the full pipeline.

This project is intentionally structured to demonstrate:

- Python backend engineering
- FastAPI API design
- Dockerized development
- PostgreSQL persistence
- Alembic migrations
- document ingestion pipelines
- metadata-driven chunking
- vector database integration
- hybrid retrieval
- configurable LLM provider abstraction
- cited RAG answer generation
- audit-friendly RAG architecture
- production-style AI system design
