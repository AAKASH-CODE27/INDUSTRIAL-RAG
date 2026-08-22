from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.failure import Failure
from app.models.failure_schemas import FailureCreate, FailureResponse, FailureUpdate
from app.models.machine import Machine


router = APIRouter(prefix="/api/failures", tags=["Failures"])


def _apply_failure_filters(
    query,
    machine_id: int | None,
    failure_code: str | None,
    failure_type: str | None,
    severity: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
):
    if machine_id is not None:
        query = query.filter(Failure.machine_id == machine_id)
    if failure_code:
        query = query.filter(Failure.failure_code == failure_code)
    if failure_type:
        query = query.filter(Failure.failure_type.ilike(f"%{failure_type}%"))
    if severity:
        query = query.filter(Failure.severity == severity)
    if start_date:
        query = query.filter(Failure.occurred_at >= start_date)
    if end_date:
        query = query.filter(Failure.occurred_at <= end_date)
    return query


@router.post("", response_model=FailureResponse, status_code=201)
def create_failure(payload: FailureCreate, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    failure = Failure(**payload.model_dump())
    db.add(failure)
    db.commit()
    db.refresh(failure)
    return failure


@router.get("/search", response_model=list[FailureResponse])
def search_failures(
    machine_id: int | None = None,
    failure_code: str | None = None,
    failure_type: str | None = None,
    severity: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Failure)
    query = _apply_failure_filters(query, machine_id, failure_code, failure_type, severity, start_date, end_date)
    return query.order_by(Failure.occurred_at.desc()).limit(limit).all()


@router.get("", response_model=list[FailureResponse])
def get_failures(
    machine_id: int | None = None,
    failure_code: str | None = None,
    failure_type: str | None = None,
    severity: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Failure)
    query = _apply_failure_filters(query, machine_id, failure_code, failure_type, severity, start_date, end_date)
    return query.order_by(Failure.occurred_at.desc()).limit(limit).all()


@router.get("/machine/{machine_id}", response_model=list[FailureResponse])
def get_machine_failures(machine_id: int, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(Failure)
        .filter(Failure.machine_id == machine_id)
        .order_by(Failure.occurred_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{failure_id}", response_model=FailureResponse)
def get_failure(failure_id: int, db: Session = Depends(get_db)):
    failure = db.query(Failure).filter(Failure.id == failure_id).first()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure record not found")
    return failure


@router.put("/{failure_id}", response_model=FailureResponse)
def update_failure(failure_id: int, payload: FailureUpdate, db: Session = Depends(get_db)):
    failure = db.query(Failure).filter(Failure.id == failure_id).first()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure record not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(failure, field, value)

    db.commit()
    db.refresh(failure)
    return failure


@router.delete("/{failure_id}")
def delete_failure(failure_id: int, db: Session = Depends(get_db)):
    failure = db.query(Failure).filter(Failure.id == failure_id).first()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure record not found")

    db.delete(failure)
    db.commit()
    return {"message": "Failure record deleted successfully"}
