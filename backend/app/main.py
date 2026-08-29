from pathlib import Path
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.anomaly import router as anomaly_router
from app.api.routes.failures import router as failures_router
from app.api.routes.health import router as health_router
from app.api.routes.maintenance import router as maintenance_router
from app.api.routes.machines import router as machines_router
from app.api.routes.sensors import router as sensors_router
from app.core.config import APP_ENV, APP_NAME, CORS_ALLOWED_ORIGINS
from app.core.database import Base, engine
from app.core.logging_config import get_logger, setup_logging
from app.api.rag import router as rag_router
from app.api.routes.chat import router as chat_router


setup_logging()
logger = get_logger(__name__)
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Industrial Maintenance AI",
    description="Multimodal RAG-based Industrial Maintenance Intelligence System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.middleware("http")
def add_request_timing(request: Request, call_next):
    started_at = time.perf_counter()
    response = None
    try:
        response = call_next(request)
        return response
    except Exception as exc:  # pragma: no cover - handled by exception handlers below
        logger.exception("Unhandled request error: method=%s path=%s", request.method, request.url.path)
        raise exc
    finally:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "HTTP request: method=%s path=%s status=%s elapsed_ms=%.1f",
            request.method,
            request.url.path,
            getattr(response, "status_code", "error"),
            elapsed_ms,
        )


def _sanitize_validation_errors(errors):
    def normalize(value):
        if isinstance(value, dict):
            return {str(key): normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        if isinstance(value, tuple):
            return [normalize(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    return [normalize(error) for error in errors]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    sanitized_errors = _sanitize_validation_errors(exc.errors())
    logger.warning("Validation error: method=%s path=%s errors=%s", request.method, request.url.path, sanitized_errors)
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "message": "Request validation failed.",
                "errors": sanitized_errors,
            }
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error: method=%s path=%s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application error: method=%s path=%s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred."},
    )


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")


app.include_router(health_router)
app.include_router(machines_router)
app.include_router(sensors_router)
app.include_router(anomaly_router)
app.include_router(failures_router)
app.include_router(maintenance_router)
app.include_router(rag_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Industrial Maintenance AI API",
        "status": "running",
        "environment": APP_ENV,
        "service": APP_NAME,
    }


@app.get("/api/db-test")
def database_test():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
    except SQLAlchemyError as exc:
        logger.exception("Database probe failed")
        raise exc

    return {
        "database": "connected",
        "test_result": value,
    }


logger.info("Application startup complete: service=%s environment=%s", APP_NAME, APP_ENV)