from __future__ import annotations

from sqlalchemy.orm import Session

from app.ml.anomaly_detector import SensorAnomalyDetector
from app.ml.feature_engineering import dataframe_from_sensor_records
from app.ml.health_score import calculate_health_score
from app.models.machine import Machine
from app.models.sensor import SensorReading


def get_recent_sensor_readings(db: Session, machine_id: int, limit: int = 20) -> list[SensorReading]:
    return (
        db.query(SensorReading)
        .filter(SensorReading.machine_id == machine_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_latest_sensor_reading(db: Session, machine_id: int) -> SensorReading | None:
    return (
        db.query(SensorReading)
        .filter(SensorReading.machine_id == machine_id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )


def compute_machine_health(db: Session, machine: Machine, lookback: int = 50) -> dict[str, object]:
    readings = get_recent_sensor_readings(db, machine.id, limit=lookback)

    if not readings:
        return {
            "machine_id": machine.id,
            "machine_code": machine.machine_code,
            "health_score": 100,
            "health_status": "excellent",
            "anomaly_detected": False,
            "anomaly_score": 0.0,
        }

    records = [
        {
            "timestamp": row.timestamp,
            "temperature": row.temperature,
            "vibration": row.vibration,
            "pressure": row.pressure,
            "rpm": row.rpm,
            "motor_current": row.motor_current,
        }
        for row in reversed(readings)
    ]

    df = dataframe_from_sensor_records(records)
    detector = SensorAnomalyDetector()
    anomaly = detector.analyze(df)

    latest = records[-1]
    health = calculate_health_score(
        temperature=float(latest["temperature"]),
        vibration=float(latest["vibration"]),
        pressure=float(latest["pressure"]),
        rpm=float(latest["rpm"]),
        motor_current=float(latest["motor_current"]),
        anomaly_score=float(anomaly["anomaly_score"]),
    )

    return {
        "machine_id": machine.id,
        "machine_code": machine.machine_code,
        "health_score": health["health_score"],
        "health_status": health["health_status"],
        "anomaly_detected": bool(anomaly["is_anomaly"]),
        "anomaly_score": float(anomaly["anomaly_score"]),
    }
