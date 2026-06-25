# ragops-document-intelligence

A production-style RAGOps/document intelligence platform for ingesting complex documents, chunking with metadata, indexing into a vector database, retrieving relevant context, generating cited answers, and evaluating RAG quality.

## Current milestone

Milestone 0: backend foundation.

This milestone sets up:

- FastAPI backend
- PostgreSQL
- Qdrant
- Redis
- Docker Compose
- Structured console logs
- Local mounted file logs
- Dependency health checks

## Why PostgreSQL?

PostgreSQL is the default relational database for this project because it is production-friendly, Docker-friendly, widely used in modern backend and AI systems, and supports JSONB/indexing for metadata, evaluator outputs, audit traces, and model results.

The database layer will use SQLAlchemy and Alembic, so the relational backend could be adapted later if required. However, v1 intentionally focuses only on PostgreSQL.

## Why Qdrant?

Qdrant is used as the vector database for document chunk embeddings and similarity search. PostgreSQL remains the source of truth for document metadata and audit history.

## Why Redis?

Redis is used for temporary runtime data such as cache entries, rate-limit counters, job status, and dashboard counters. Durable audit history belongs in PostgreSQL, not Redis.

## Logging strategy

The application logs to:

1. structured stdout logs for Docker and future centralized log collectors,
2. mounted local file logs for debugging,
3. PostgreSQL audit tables later for durable AI workflow history.

Local file logs are written to:

```txt
./logs/app.log
./logs/errors.log