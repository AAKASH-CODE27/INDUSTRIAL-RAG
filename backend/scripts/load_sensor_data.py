import pandas as pd
from pathlib import Path
from app.core.database import SessionLocal
from app.models.sensor import SensorReading
from app.models.machine import Machine

def main():
    db = SessionLocal()
    try:
        # Check if machines exist
        machine = db.query(Machine).first()
        if not machine:
            print("No machines found. Please run seed_industrial_data.py first.")
            return

        machine_id = machine.id
        
        # Paths to CSVs
        base_dir = Path(__file__).resolve().parents[1]
        sensor_dir = base_dir / "data" / "sensors"
        
        # Load one of the datasets for realistic chat context
        # Failure dataset gives the most interesting context
        csv_path = sensor_dir / "failure_sensor_data.csv"
        
        if not csv_path.exists():
            print(f"File not found: {csv_path}. Run generate_sensor_data.py first.")
            return
            
        print(f"Loading sensor data from {csv_path} for machine {machine_id}...")
        df = pd.read_csv(csv_path)
        
        # Clear existing
        db.query(SensorReading).delete()
        db.commit()
        
        # Insert new
        records = df.to_dict("records")
        for r in records:
            r['timestamp'] = pd.to_datetime(r['timestamp']).to_pydatetime()
        db.bulk_insert_mappings(SensorReading, records)
        db.commit()
        
        count = db.query(SensorReading).count()
        print(f"Successfully loaded {count} sensor readings.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
