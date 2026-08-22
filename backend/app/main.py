from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.anomaly import router as anomaly_router
from app.api.routes.failures import router as failures_router
from app.api.routes.health import router as health_router
from app.api.routes.maintenance import router as maintenance_router
from app.api.routes.machines import router as machines_router
from app.api.routes.sensors import router as sensors_router
from app.core.database import engine, Base
from app.core.logging_config import setup_logging
from app.models.failure import Failure
from app.models.maintenance import MaintenanceRecord
from app.models.machine import Machine
from app.models.sensor import SensorReading

# Create database tables
setup_logging()
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Industrial Maintenance AI",
    description="Multimodal RAG-based Industrial Maintenance Intelligence System",
    version="1.0.0"
)


app.include_router(health_router)
app.include_router(machines_router)
app.include_router(sensors_router)
app.include_router(anomaly_router)
app.include_router(failures_router)
app.include_router(maintenance_router)

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