from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    machine_id: int = Field(gt=0)
    maintenance_type: str
    description: str
    findings: str
    action_taken: str
    parts_replaced: str | None = None
    technician: str
    cost: float = Field(default=0.0, ge=0)
    downtime_minutes: int = Field(default=0, ge=0)
    performed_at: datetime
    next_due_at: datetime | None = None


class MaintenanceUpdate(BaseModel):
    maintenance_type: str | None = None
    description: str | None = None
    findings: str | None = None
    action_taken: str | None = None
    parts_replaced: str | None = None
    technician: str | None = None
    cost: float | None = Field(default=None, ge=0)
    downtime_minutes: int | None = Field(default=None, ge=0)
    performed_at: datetime | None = None
    next_due_at: datetime | None = None


class MaintenanceResponse(BaseModel):
    id: int
    machine_id: int
    maintenance_type: str
    description: str
    findings: str
    action_taken: str
    parts_replaced: str | None
    technician: str
    cost: float
    downtime_minutes: int
    performed_at: datetime
    next_due_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
