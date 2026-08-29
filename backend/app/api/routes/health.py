from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Health"],
)


def _database_status() -> tuple[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok", "Database connection is available."
    except SQLAlchemyError as exc:
        logger.warning("Health check database probe failed: %s", exc)
        return "error", "Database connection is unavailable."


@router.get("/health")
def health_check():
    database_status, database_message = _database_status()
    return {
        "status": "ok",
        "service": "industrial-maintenance-ai",
        "checks": {
            "database": {
                "status": database_status,
                "message": database_message,
            }
        },
    }


@router.get("/health/ready")
def readiness_check():
    database_status, database_message = _database_status()
    checks = {
        "database": {
            "status": database_status,
            "message": database_message,
        },
    }
    overall_status = "ready" if database_status == "ok" else "degraded"
    return {
        "status": overall_status,
        "service": "industrial-maintenance-ai",
        "checks": checks,
    }