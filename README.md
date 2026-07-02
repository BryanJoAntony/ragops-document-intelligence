# ragops-document-intelligence

A production-style RAGOps/document intelligence platform for ingesting documents, storing metadata, parsing content, chunking with traceability, indexing chunks into a vector database, retrieving relevant context, generating cited answers, and preparing for RAG quality evaluation.

This project is being built milestone by milestone to demonstrate backend engineering for AI systems, not just a basic chatbot demo.

## Current public milestone

Milestone 2: retrieval and cited answer foundation.

This public milestone combines the internal embeddings, Qdrant indexing, vector search, cited local answer generation, and audit logging work into one GitHub milestone after the document ingestion foundation.

## What this milestone includes

- FastAPI backend
- Docker Compose development setup
- PostgreSQL relational persistence
- Redis runtime/cache layer
- Qdrant vector database service
- SQLAlchemy ORM setup
- Alembic database migrations
- Document upload endpoint
- Local file storage abstraction
- SHA-256 file hashing
- Duplicate document detection
- TXT parsing
- PDF parsing
- DOCX parsing
- Document chunking
- Chunk-level metadata
- Generated document and chunk tags
- Sentence-transformer embeddings
- Qdrant vector indexing
- Vector search over document chunks
- Basic cited RAG answer generation
- Query audit logging in PostgreSQL
- LLM call logging in PostgreSQL
- pytest test foundation
- Dependency health checks
- Structured logging foundation

## Why this matters

A RAG system needs more than an LLM call.

Before answer quality can be improved, the system needs to support:

- reliable document ingestion
- traceable chunks
- vector indexing
- retrieval over stored chunks
- cited answer generation
- query audit history
- model/call logging
- testable service boundaries

This milestone moves the project from document ingestion into the first working retrieval and answer flow.

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
        v
Answer generation service
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
- retrieval service: retrieves relevant chunks
- answer generation service: creates conservative cited local answers
- audit service: records query and model-call history in PostgreSQL

This structure keeps routes thin and prepares the project for later orchestration, evaluation, dashboards, background jobs, and agent/MCP-style tools.

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

## Roadmap

Planned next milestones:

- hybrid retrieval
- BM25 retrieval
- fuzzy retrieval
- configurable answer providers
- multi-provider orchestration
- retrieval evaluation datasets
- citation validation
- async ingestion jobs
- metadata filtering
- RAGOps dashboard
- agent/MCP-style tool exposure

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
- cited RAG answer generation
- audit-friendly RAG architecture
- production-style AI system design
