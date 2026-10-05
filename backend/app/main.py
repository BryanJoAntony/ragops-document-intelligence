import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.citations import router as citations_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.documents import router as documents_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.query import router as query_router
from app.api.routes.routing import router as routing_router
from app.core.config import get_settings
from app.core.logging import setup_logging

setup_logging()

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.11.0",
    description="Production-style RAGOps document intelligence platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(evaluations_router)
app.include_router(citations_router)
app.include_router(jobs_router)
app.include_router(dashboard_router)
app.include_router(routing_router)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("RAGOps API started")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "ragops-document-intelligence API is running",
        "docs": "/docs",
        "health": "/health",
        "documents": "/documents",
        "query": "/query/ask",
        "evaluations": "/evaluations/run",
        "citations": "/citations/validate-rag",
        "jobs": "/jobs/{job_id}",
        "async_evaluation": "/jobs/evaluations/run",
        "dashboard": "/dashboard/overview",
        "routing": "/routing/answer-plan",
    }

