import logging

from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.logging import setup_logging

setup_logging()

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Production-style RAGOps document intelligence platform.",
)

app.include_router(health_router)
app.include_router(documents_router)


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
    }