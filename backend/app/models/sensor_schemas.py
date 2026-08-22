from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorReadingCreate(BaseModel):
    machine_id: int = Field(gt=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    motor_current: float


class SensorReadingResponse(BaseModel):
    id: int
    machine_id: int
    timestamp: datetime
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    motor_current: float

    model_config = ConfigDict(from_attributes=True)


class SensorBulkCreate(BaseModel):
    readings: list[SensorReadingCreate] = Field(min_length=1)
