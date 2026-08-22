from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.machine import Machine
from app.models.sensor import SensorReading
from app.models.sensor_schemas import SensorBulkCreate, SensorReadingCreate, SensorReadingResponse


logger = get_logger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])


@router.post("", response_model=SensorReadingResponse, status_code=201)
def create_sensor_reading(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == reading.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    sensor_reading = SensorReading(**reading.model_dump())
    db.add(sensor_reading)
    db.commit()
    db.refresh(sensor_reading)
    return sensor_reading


@router.post("/bulk", status_code=201)
def bulk_create_sensor_readings(payload: SensorBulkCreate, db: Session = Depends(get_db)):
    machine_ids = sorted({item.machine_id for item in payload.readings})

    existing_machine_ids = {
        machine_id
        for (machine_id,) in db.query(Machine.id).filter(Machine.id.in_(machine_ids)).all()
    }

    missing_ids = [machine_id for machine_id in machine_ids if machine_id not in existing_machine_ids]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail={"message": "Some machine IDs do not exist", "machine_ids": missing_ids},
        )

    objects = [SensorReading(**item.model_dump()) for item in payload.readings]

    try:
        db.bulk_save_objects(objects)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Bulk sensor insert failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to insert bulk sensor readings") from exc

    return {
        "message": "Sensor readings inserted successfully",
        "inserted": len(objects),
    }


@router.post("/upload-csv", status_code=201)
async def upload_sensor_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    required_columns = {
        "machine_id",
        "timestamp",
        "temperature",
        "vibration",
        "pressure",
        "rpm",
        "motor_current",
    }

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {exc}") from exc

    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing required columns", "missing_columns": missing_columns},
        )

    parsed_rows: list[dict[str, object]] = []
    row_errors: list[dict[str, object]] = []

    for idx, row in df.iterrows():
        row_number = int(idx) + 2
        try:
            machine_id = int(row["machine_id"])
            if machine_id <= 0:
                raise ValueError("machine_id must be greater than 0")

            timestamp = pd.to_datetime(row["timestamp"], errors="raise").to_pydatetime()
            temperature = float(row["temperature"])
            vibration = float(row["vibration"])
            pressure = float(row["pressure"])
            rpm = float(row["rpm"])
            motor_current = float(row["motor_current"])

            parsed_rows.append(
                {
                    "machine_id": machine_id,
                    "timestamp": timestamp,
                    "temperature": temperature,
                    "vibration": vibration,
                    "pressure": pressure,
                    "rpm": rpm,
                    "motor_current": motor_current,
                }
            )
        except Exception as exc:
            row_errors.append({"row": row_number, "error": str(exc)})

    if row_errors:
        logger.warning("CSV validation failed with %s malformed rows", len(row_errors))
        raise HTTPException(
            status_code=400,
            detail={"message": "Malformed CSV rows detected", "errors": row_errors},
        )

    machine_ids = sorted({int(item["machine_id"]) for item in parsed_rows})
    existing_machine_ids = {
        machine_id
        for (machine_id,) in db.query(Machine.id).filter(Machine.id.in_(machine_ids)).all()
    }

    missing_ids = [machine_id for machine_id in machine_ids if machine_id not in existing_machine_ids]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail={"message": "Machine IDs not found", "machine_ids": missing_ids},
        )

    objects = [SensorReading(**row) for row in parsed_rows]

    try:
        db.bulk_save_objects(objects)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("CSV ingestion failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to ingest CSV data") from exc

    logger.info("CSV ingestion completed: %s readings inserted", len(objects))
    return {
        "message": "Sensor readings inserted successfully",
        "inserted": len(objects),
    }


@router.get("", response_model=list[SensorReadingResponse])
def get_sensor_readings(limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/machine/{machine_id}", response_model=list[SensorReadingResponse])
def get_machine_readings(machine_id: int, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(SensorReading)
        .filter(SensorReading.machine_id == machine_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/machine/{machine_id}/history", response_model=list[SensorReadingResponse])
def get_machine_history(
    machine_id: int,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    query = db.query(SensorReading).filter(SensorReading.machine_id == machine_id)

    if start_time:
        query = query.filter(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.filter(SensorReading.timestamp <= end_time)

    return query.order_by(SensorReading.timestamp.desc()).limit(limit).all()


@router.get("/machine/{machine_id}/summary")
def get_machine_sensor_summary(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    stats = (
        db.query(
            func.count(SensorReading.id),
            func.min(SensorReading.temperature),
            func.max(SensorReading.temperature),
            func.avg(SensorReading.temperature),
            func.min(SensorReading.vibration),
            func.max(SensorReading.vibration),
            func.avg(SensorReading.vibration),
            func.min(SensorReading.pressure),
            func.max(SensorReading.pressure),
            func.avg(SensorReading.pressure),
            func.min(SensorReading.rpm),
            func.max(SensorReading.rpm),
            func.avg(SensorReading.rpm),
            func.min(SensorReading.motor_current),
            func.max(SensorReading.motor_current),
            func.avg(SensorReading.motor_current),
        )
        .filter(SensorReading.machine_id == machine_id)
        .one()
    )

    count = int(stats[0] or 0)

    def metric(min_val, max_val, mean_val):
        return {
            "min": float(min_val) if min_val is not None else None,
            "max": float(max_val) if max_val is not None else None,
            "mean": float(mean_val) if mean_val is not None else None,
        }

    return {
        "machine_id": machine_id,
        "reading_count": count,
        "temperature": metric(stats[1], stats[2], stats[3]),
        "vibration": metric(stats[4], stats[5], stats[6]),
        "pressure": metric(stats[7], stats[8], stats[9]),
        "rpm": metric(stats[10], stats[11], stats[12]),
        "motor_current": metric(stats[13], stats[14], stats[15]),
    }


@router.get("/{sensor_id}", response_model=SensorReadingResponse)
def get_sensor_reading(sensor_id: int, db: Session = Depends(get_db)):
    reading = db.query(SensorReading).filter(SensorReading.id == sensor_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Sensor reading not found")
    return reading


@router.delete("/{sensor_id}")
def delete_sensor_reading(sensor_id: int, db: Session = Depends(get_db)):
    reading = db.query(SensorReading).filter(SensorReading.id == sensor_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Sensor reading not found")

    db.delete(reading)
    db.commit()
    return {"message": "Sensor reading deleted successfully"}
