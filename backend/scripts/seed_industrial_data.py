from __future__ import annotations

from datetime import datetime, timedelta
from random import choice, randint, uniform
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import Base, SessionLocal, engine
from app.models.failure import Failure
from app.models.machine import Machine
from app.models.maintenance import MaintenanceRecord


MACHINE_DATA = [
    {"machine_code": "CNC-001", "name": "CNC Milling Machine", "machine_type": "CNC", "location": "Production Floor A", "status": "active"},
    {"machine_code": "CNC-002", "name": "CNC Turning Center", "machine_type": "CNC", "location": "Production Floor B", "status": "active"},
    {"machine_code": "LATHE-001", "name": "Precision Lathe", "machine_type": "Lathe", "location": "Machining Bay", "status": "active"},
    {"machine_code": "PRESS-001", "name": "Hydraulic Press", "machine_type": "Press", "location": "Forming Line", "status": "active"},
    {"machine_code": "MILL-001", "name": "Vertical Mill", "machine_type": "Mill", "location": "Tool Room", "status": "active"},
]

FAILURE_LIBRARY = [
    ("E104", "Spindle vibration", "High", "High vibration, temperature increase", "Spindle bearing degradation", "Replace bearing and check alignment"),
    ("E211", "Motor overheating", "High", "Motor heat rise, current spike", "Cooling airflow blockage", "Clean ducts and replace cooling fan"),
    ("E307", "Belt wear", "Medium", "Slip noise, RPM instability", "Drive belt wear and slack", "Replace and tension drive belt"),
    ("E415", "Shaft misalignment", "High", "Persistent vibration, uneven wear", "Coupling misalignment", "Laser align shaft and coupling"),
    ("E522", "Hydraulic pressure loss", "Critical", "Pressure drop, force reduction", "Hydraulic seal leakage", "Replace seals and refill fluid"),
    ("E266", "Tool imbalance", "Medium", "Tool chatter, surface defects", "Tool holder imbalance", "Rebalance and calibrate tool assembly"),
    ("E341", "Lubrication failure", "High", "Heat increase, friction noise", "Lubrication line blockage", "Flush lubrication system and replace filter"),
    ("E487", "Electrical overload", "Critical", "Breaker trips, high current", "Motor winding stress", "Inspect winding and adjust load profile"),
    ("E593", "Cooling system failure", "High", "Coolant temperature rise", "Pump degradation", "Replace coolant pump and purge air"),
    ("E678", "Excessive vibration", "High", "Oscillation exceeds threshold", "Foundation bolt looseness", "Retorque mounts and inspect frame"),
]

MAINTENANCE_TYPES = ["preventive", "corrective", "predictive", "inspection", "emergency"]
TECHNICIANS = ["Technician-01", "Technician-02", "Technician-03", "Technician-04"]


def seed_machines(db) -> list[Machine]:
    machines: list[Machine] = []

    for item in MACHINE_DATA:
        machine = db.query(Machine).filter(Machine.machine_code == item["machine_code"]).first()
        if machine is None:
            machine = Machine(**item)
            db.add(machine)
            db.flush()
        machines.append(machine)

    return machines


def seed_failures(db, machines: list[Machine], total: int = 20) -> None:
    now = datetime.utcnow()

    for i in range(total):
        machine = choice(machines)
        code, f_type, severity, symptoms, cause, resolution = choice(FAILURE_LIBRARY)
        occurred_at = now - timedelta(days=randint(2, 220), hours=randint(1, 20))
        downtime = randint(25, 420)

        record = Failure(
            machine_id=machine.id,
            failure_code=code,
            failure_type=f_type,
            severity=severity,
            symptoms=symptoms,
            root_cause=cause,
            resolution=resolution,
            downtime_minutes=downtime,
            occurred_at=occurred_at,
            resolved_at=occurred_at + timedelta(minutes=downtime),
        )
        db.add(record)


def seed_maintenance(db, machines: list[Machine], total: int = 40) -> None:
    now = datetime.utcnow()

    for i in range(total):
        machine = choice(machines)
        m_type = choice(MAINTENANCE_TYPES)
        performed_at = now - timedelta(days=randint(1, 180), hours=randint(1, 10))

        record = MaintenanceRecord(
            machine_id=machine.id,
            maintenance_type=m_type,
            description=f"{m_type.title()} maintenance on {machine.machine_code}",
            findings=choice([
                "Bearing wear detected",
                "Belt tension outside tolerance",
                "Minor shaft runout",
                "Hydraulic line seepage",
                "Coolant contamination",
                "Electrical terminal heating",
            ]),
            action_taken=choice([
                "Replaced worn component and recalibrated",
                "Performed alignment and balancing",
                "Cleaned and restored lubrication path",
                "Adjusted load and reset control parameters",
                "Replaced seals and pressure tested",
            ]),
            parts_replaced=choice([
                "Spindle bearing",
                "Drive belt",
                "Hydraulic seal kit",
                "Cooling fan",
                "None",
            ]),
            technician=choice(TECHNICIANS),
            cost=round(uniform(120.0, 1900.0), 2),
            downtime_minutes=randint(10, 360),
            performed_at=performed_at,
            next_due_at=performed_at + timedelta(days=randint(14, 120)),
        )
        db.add(record)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        machines = seed_machines(db)
        seed_failures(db, machines, total=20)
        seed_maintenance(db, machines, total=40)
        db.commit()
        print("Industrial seed data inserted successfully")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
