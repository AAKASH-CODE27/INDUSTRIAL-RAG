from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml.anomaly_detector import SensorAnomalyDetector
from app.ml.feature_engineering import dataframe_from_sensor_records
from app.ml.health_score import calculate_health_score
from app.models.machine import Machine
from app.models.sensor import SensorReading


router = APIRouter(prefix="/api/anomaly", tags=["Anomaly"])


@router.post("/analyze/{machine_id}")
def analyze_machine_anomaly(machine_id: int, lookback: int = 50, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.machine_id == machine_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(lookback)
        .all()
    )

    if not readings:
        raise HTTPException(status_code=404, detail="No sensor readings available for this machine")

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
        "is_anomaly": anomaly["is_anomaly"],
        "anomaly_score": anomaly["anomaly_score"],
        "severity": anomaly["severity"],
        "reasons": anomaly["reasons"],
        "health_score": health["health_score"],
        "health_status": health["health_status"],
    }
