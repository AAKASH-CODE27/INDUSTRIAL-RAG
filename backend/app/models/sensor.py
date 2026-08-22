from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
        index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    vibration: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    pressure: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    rpm: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    motor_current: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )