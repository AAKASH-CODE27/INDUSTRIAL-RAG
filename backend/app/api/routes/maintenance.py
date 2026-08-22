from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.machine import Machine
from app.models.maintenance import MaintenanceRecord
from app.models.maintenance_schemas import MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate


router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])


@router.post("", response_model=MaintenanceResponse, status_code=201)
def create_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    record = MaintenanceRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[MaintenanceResponse])
def get_maintenance_records(
    machine_id: int | None = None,
    maintenance_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(MaintenanceRecord)

    if machine_id is not None:
        query = query.filter(MaintenanceRecord.machine_id == machine_id)
    if maintenance_type:
        query = query.filter(MaintenanceRecord.maintenance_type == maintenance_type)
    if start_date:
        query = query.filter(MaintenanceRecord.performed_at >= start_date)
    if end_date:
        query = query.filter(MaintenanceRecord.performed_at <= end_date)

    return query.order_by(MaintenanceRecord.performed_at.desc()).limit(limit).all()


@router.get("/machine/{machine_id}", response_model=list[MaintenanceResponse])
def get_machine_maintenance(machine_id: int, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.machine_id == machine_id)
        .order_by(MaintenanceRecord.performed_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance_record(maintenance_id: int, db: Session = Depends(get_db)):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return record


@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance_record(maintenance_id: int, payload: MaintenanceUpdate, db: Session = Depends(get_db)):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{maintenance_id}")
def delete_maintenance_record(maintenance_id: int, db: Session = Depends(get_db)):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    db.delete(record)
    db.commit()
    return {"message": "Maintenance record deleted successfully"}
