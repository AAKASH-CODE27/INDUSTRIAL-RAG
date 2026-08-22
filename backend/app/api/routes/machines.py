from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.failure import Failure
from app.models.maintenance import MaintenanceRecord
from app.models.machine import Machine
from app.models.schemas import (
    MachineCreate,
    MachineUpdate,
    MachineResponse
)
from app.models.sensor import SensorReading
from app.services.sensor_service import compute_machine_health


router = APIRouter(
    prefix="/api/machines",
    tags=["Machines"]
)


@router.post(
    "",
    response_model=MachineResponse,
    status_code=201
)
def create_machine(
    machine_data: MachineCreate,
    db: Session = Depends(get_db)
):
    existing_machine = (
        db.query(Machine)
        .filter(Machine.machine_code == machine_data.machine_code)
        .first()
    )

    if existing_machine:
        raise HTTPException(
            status_code=400,
            detail="Machine code already exists"
        )

    machine = Machine(
        machine_code=machine_data.machine_code,
        name=machine_data.name,
        machine_type=machine_data.machine_type,
        location=machine_data.location,
        status=machine_data.status
    )

    db.add(machine)
    db.commit()
    db.refresh(machine)

    return machine


@router.get(
    "",
    response_model=list[MachineResponse]
)
def get_machines(
    db: Session = Depends(get_db)
):
    machines = db.query(Machine).all()

    return machines


@router.get(
    "/{machine_id}",
    response_model=MachineResponse
)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db)
):
    machine = (
        db.query(Machine)
        .filter(Machine.id == machine_id)
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=404,
            detail="Machine not found"
        )

    return machine


@router.put(
    "/{machine_id}",
    response_model=MachineResponse
)
def update_machine(
    machine_id: int,
    machine_data: MachineUpdate,
    db: Session = Depends(get_db)
):
    machine = (
        db.query(Machine)
        .filter(Machine.id == machine_id)
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=404,
            detail="Machine not found"
        )

    update_data = machine_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(machine, field, value)

    db.commit()
    db.refresh(machine)

    return machine


@router.delete(
    "/{machine_id}"
)
def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db)
):
    machine = (
        db.query(Machine)
        .filter(Machine.id == machine_id)
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=404,
            detail="Machine not found"
        )

    db.delete(machine)
    db.commit()

    return {
        "message": "Machine deleted successfully"
    }


@router.get("/{machine_id}/health")
def get_machine_health(
    machine_id: int,
    db: Session = Depends(get_db)
):
    machine = (
        db.query(Machine)
        .filter(Machine.id == machine_id)
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=404,
            detail="Machine not found"
        )

    return compute_machine_health(db, machine)


@router.get("/{machine_id}/overview")
def get_machine_overview(
    machine_id: int,
    db: Session = Depends(get_db)
):
    machine = (
        db.query(Machine)
        .filter(Machine.id == machine_id)
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=404,
            detail="Machine not found"
        )

    health = compute_machine_health(db, machine)

    recent_sensor_readings = (
        db.query(SensorReading)
        .filter(SensorReading.machine_id == machine_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(10)
        .all()
    )

    recent_failures = (
        db.query(Failure)
        .filter(Failure.machine_id == machine_id)
        .order_by(Failure.occurred_at.desc())
        .limit(10)
        .all()
    )

    recent_maintenance = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.machine_id == machine_id)
        .order_by(MaintenanceRecord.performed_at.desc())
        .limit(10)
        .all()
    )

    return {
        "machine": {
            "id": machine.id,
            "machine_code": machine.machine_code,
            "name": machine.name,
            "machine_type": machine.machine_type,
            "location": machine.location,
            "status": machine.status,
        },
        "health": {
            "score": health["health_score"],
            "status": health["health_status"],
            "anomaly_detected": health["anomaly_detected"],
            "anomaly_score": health["anomaly_score"],
        },
        "recent_sensor_readings": [
            {
                "id": reading.id,
                "timestamp": reading.timestamp,
                "temperature": reading.temperature,
                "vibration": reading.vibration,
                "pressure": reading.pressure,
                "rpm": reading.rpm,
                "motor_current": reading.motor_current,
            }
            for reading in recent_sensor_readings
        ],
        "recent_failures": [
            {
                "id": failure.id,
                "failure_code": failure.failure_code,
                "failure_type": failure.failure_type,
                "severity": failure.severity,
                "symptoms": failure.symptoms,
                "root_cause": failure.root_cause,
                "resolution": failure.resolution,
                "downtime_minutes": failure.downtime_minutes,
                "occurred_at": failure.occurred_at,
                "resolved_at": failure.resolved_at,
            }
            for failure in recent_failures
        ],
        "recent_maintenance": [
            {
                "id": record.id,
                "maintenance_type": record.maintenance_type,
                "description": record.description,
                "findings": record.findings,
                "action_taken": record.action_taken,
                "parts_replaced": record.parts_replaced,
                "technician": record.technician,
                "cost": record.cost,
                "downtime_minutes": record.downtime_minutes,
                "performed_at": record.performed_at,
                "next_due_at": record.next_due_at,
            }
            for record in recent_maintenance
        ],
    }