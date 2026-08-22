from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MachineCreate(BaseModel):
    machine_code: str
    name: str
    machine_type: str
    location: str | None = None
    status: str = "active"


class MachineUpdate(BaseModel):
    machine_code: str | None = None
    name: str | None = None
    machine_type: str | None = None
    location: str | None = None
    status: str | None = None


class MachineResponse(BaseModel):
    id: int
    machine_code: str
    name: str
    machine_type: str
    location: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)