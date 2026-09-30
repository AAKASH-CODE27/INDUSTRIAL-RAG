import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.machine import Machine
from app.models.sensor import SensorReading


def main():
    db = SessionLocal()
    try:
        # Retrieve all machines in stable ID order
        machines = db.query(Machine).order_by(Machine.id).all()
        if not machines:
            print("No machines found. Please run seed_industrial_data.py first.")
            return

        # Paths to CSVs
        base_dir = Path(__file__).resolve().parents[1]
        sensor_dir = base_dir / "data" / "sensors"

        # Load one of the datasets for realistic chat context
        # Failure dataset gives the most interesting context
        csv_path = sensor_dir / "failure_sensor_data.csv"

        if not csv_path.exists():
            print(f"File not found: {csv_path}. Run generate_sensor_data.py first.")
            return

        print(f"Loading sensor data from {csv_path} across {len(machines)} machines...")
        df = pd.read_csv(csv_path)

        # Clear existing
        db.query(SensorReading).delete()
        db.commit()

        # Distribute records round-robin across available machines
        records = df.to_dict("records")
        for index, record in enumerate(records):
            machine = machines[index % len(machines)]
            record["machine_id"] = machine.id
            record["timestamp"] = pd.to_datetime(record["timestamp"]).to_pydatetime()

        db.bulk_insert_mappings(SensorReading, records)
        db.commit()

        total_inserted = db.query(SensorReading).count()
        print(f"Successfully loaded {total_inserted} sensor readings (expected: 240).")
        print("Reading count per machine:")
        for m in machines:
            count = db.query(SensorReading).filter(SensorReading.machine_id == m.id).count()
            print(f"  - Machine ID {m.id} ({m.machine_code}): {count} readings")

    finally:
        db.close()


if __name__ == "__main__":
    main()
