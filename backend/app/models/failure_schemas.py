from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FailureCreate(BaseModel):
    machine_id: int = Field(gt=0)
    failure_code: str
    failure_type: str
    severity: str
    symptoms: str
    root_cause: str
    resolution: str
    downtime_minutes: int = Field(default=0, ge=0)
    occurred_at: datetime
    resolved_at: datetime | None = None


class FailureUpdate(BaseModel):
    failure_code: str | None = None
    failure_type: str | None = None
    severity: str | None = None
    symptoms: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    downtime_minutes: int | None = Field(default=None, ge=0)
    occurred_at: datetime | None = None
    resolved_at: datetime | None = None


class FailureResponse(BaseModel):
    id: int
    machine_id: int
    failure_code: str
    failure_type: str
    severity: str
    symptoms: str
    root_cause: str
    resolution: str
    downtime_minutes: int
    occurred_at: datetime
    resolved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
