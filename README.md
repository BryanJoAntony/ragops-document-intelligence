# ragops-document-intelligence

A production-style RAGOps/document intelligence platform for ingesting documents, storing metadata, parsing content, chunking with traceability, and preparing documents for retrieval, cited answer generation, and RAG quality evaluation.

This project is being built milestone by milestone to demonstrate backend engineering for AI systems, not just a basic chatbot demo.

## Current public milestone

Milestone 1: document ingestion foundation.

This public milestone combines the internal database, upload/storage, parsing, chunking, and metadata-tagging work into one GitHub milestone after the Docker backend foundation.

## What this milestone includes

* FastAPI backend
* Docker Compose development setup
* PostgreSQL relational persistence
* Redis runtime/cache layer
* Qdrant vector database service
* SQLAlchemy ORM setup
* Alembic database migrations
* Document upload endpoint
* Local file storage abstraction
* SHA-256 file hashing
* Duplicate document detection
* PostgreSQL document tracking
* TXT parsing
* PDF parsing
* DOCX parsing
* Document chunking
* Chunk-level metadata
* Generated document and chunk tags
* Dependency health checks
* Structured logging foundation

## Why this matters

A RAG system is only as reliable as its ingestion layer.

Before retrieval, embeddings, or LLM calls can be trusted, the system needs to know:

* what document was uploaded
* whether the file is a duplicate
* where the file is stored
* whether parsing succeeded
* how the text was split
* which chunk came from which document
* what metadata belongs to each chunk
* how the system can trace an answer back to source content

This milestone focuses on that foundation.

## Architecture at this milestone

```txt
User uploads document
        |
        v
FastAPI upload route
        |
        v
Document storage service
        |
        v
SHA-256 hashing + duplicate check
        |
        v
PostgreSQL document record
        |
        v
Document parser service
        |
        v
Chunking service
        |
        v
Metadata tagging service
        |
        v
PostgreSQL document_chunks
```

## Core services

The ingestion layer is split into services instead of putting everything inside FastAPI routes.

Current service responsibilities include:

* storage service: handles local file persistence
* document parser service: extracts text from supported file types
* chunking service: splits parsed text into traceable chunks
* metadata tagging service: creates basic generated tags
* ingestion service: coordinates parsing, chunking, metadata, and persistence

This keeps routes thin and makes the core logic easier to test, reuse, and later expose as background jobs or agent/MCP-style tools.

## Database foundation

PostgreSQL is used as the durable source of truth for:

* uploaded documents
* document metadata
* document chunks
* generated tags
* future query audits
* future LLM call logs
* future evaluation results

Alembic is used for database migrations so schema changes are versioned instead of being manually applied.

## Why PostgreSQL?

PostgreSQL is the default relational database for this project because it is production-friendly, Docker-friendly, widely used in backend and AI systems, and supports structured relational data plus JSONB-style metadata when needed.

In this project:

* PostgreSQL stores durable metadata and audit history.
* Qdrant stores vector embeddings.
* Redis stores temporary runtime/cache state only.

## Why Qdrant?

Qdrant is included as the vector database for future document chunk embeddings and similarity search.

PostgreSQL remains the source of truth for document records and chunk metadata. Qdrant will be used for vector retrieval, not durable business history.

## Why Redis?

Redis is used for temporary runtime data such as:

* cache entries
* rate-limit counters
* job status
* dashboard counters
* temporary runtime state

Durable audit history belongs in PostgreSQL, not Redis.

## Logging strategy

The application logs to:

1. structured stdout/stderr logs for Docker and future centralized log collectors
2. mounted local file logs for debugging
3. PostgreSQL audit tables later for durable AI workflow history

Local file logs are written to:

```txt
./logs/app.log
./logs/errors.log
```

The project avoids logging secrets, sensitive document text, and full prompts by default.

## Current API areas

At this milestone, the important API areas are:

```txt
GET  /health
GET  /health/deps

POST /documents/upload
GET  /documents
GET  /documents/{document_id}

POST /documents/{document_id}/ingest
GET  /documents/{document_id}/chunks
```

## Supported document types at this milestone

```txt
.txt
.pdf
.docx
```

## Local development

Start the full stack:

```powershell
docker compose up --build
```

Check service health:

```powershell
curl.exe http://localhost:8000/health/deps
```

Expected dependencies:

```txt
postgres: ok
redis: ok
qdrant: ok
```

Run tests:

```powershell
docker compose exec api pytest -q
```

## Milestone progress

### Public Milestone 0 — Backend foundation

Completed:

* Dockerized FastAPI backend
* PostgreSQL container
* Redis container
* Qdrant container
* Health endpoints
* Dependency health checks
* Structured logging foundation

### Public Milestone 1 — Document ingestion foundation

Completed:

* SQLAlchemy + Alembic schema foundation
* documents table
* document_chunks table
* upload endpoint
* local storage abstraction
* file hashing
* duplicate detection
* parser service
* chunking service
* metadata tagging
* ingestion endpoint
* chunk inspection endpoint

## Roadmap

Planned next milestones:

* embeddings generation
* Qdrant indexing
* vector search
* BM25 retrieval
* fuzzy retrieval
* hybrid retrieval
* cited RAG answer generation
* query audit logging
* LLM provider abstraction
* multi-provider orchestration
* retrieval evaluation datasets
* citation validation
* async ingestion jobs
* metadata filtering
* RAGOps dashboard
* agent/MCP-style tool exposure

## Project goal

The goal is to build a production-style document intelligence platform where users can upload documents, parse and chunk them, index them for retrieval, ask cited questions, inspect retrieval decisions, compare answer providers, evaluate RAG quality, and monitor the full pipeline.

This project is intentionally structured to demonstrate:

* Python backend engineering
* FastAPI API design
* Dockerized development
* PostgreSQL persistence
* Alembic migrations
* document ingestion pipelines
* metadata-driven chunking
* vector database integration
* audit-friendly RAG architecture
* production-style AI system design
