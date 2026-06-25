import logging
from typing import Any

from fastapi import APIRouter
from qdrant_client import QdrantClient
from redis import Redis
from sqlalchemy import create_engine, text

from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().service_name}


@router.get("/deps")
def dependency_health_check() -> dict[str, Any]:
    settings = get_settings()

    results = {
        "postgres": _check_postgres(settings.database_url),
        "redis": _check_redis(settings.redis_url),
        "qdrant": _check_qdrant(settings.qdrant_url),
    }

    overall_status = "ok" if all(item["ok"] for item in results.values()) else "degraded"

    return {
        "status": overall_status,
        "dependencies": results,
    }


def _check_postgres(database_url: str) -> dict[str, Any]:
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"ok": True}
    except Exception as exc:
        logger.exception("PostgreSQL health check failed")
        return {"ok": False, "error": str(exc)}


def _check_redis(redis_url: str) -> dict[str, Any]:
    try:
        client = Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()

        return {"ok": True}
    except Exception as exc:
        logger.exception("Redis health check failed")
        return {"ok": False, "error": str(exc)}


def _check_qdrant(qdrant_url: str) -> dict[str, Any]:
    try:
        client = QdrantClient(url=qdrant_url, timeout=2)
        client.get_collections()

        return {"ok": True}
    except Exception as exc:
        logger.exception("Qdrant health check failed")
        return {"ok": False, "error": str(exc)}