from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.health import router as health_router
from app.core.database import engine, Base
from app.models.machine import Machine


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Industrial Maintenance AI",
    description="Multimodal RAG-based Industrial Maintenance Intelligence System",
    version="1.0.0"
)


app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "Industrial Maintenance AI API",
        "status": "running"
    }


@app.get("/api/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test_result": value
    }