from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "sensors"


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _generate_normal_rows(machine_id: int, count: int) -> list[dict[str, float | int | datetime]]:
    rows = []
    timestamp = datetime.utcnow() - timedelta(minutes=count)

    for i in range(count):
        drift = i * 0.005
        rows.append(
            {
                "machine_id": machine_id,
                "timestamp": timestamp + timedelta(minutes=i),
                "temperature": round(_bounded(random.gauss(62 + drift, 1.2), 58, 66), 2),
                "vibration": round(_bounded(random.gauss(2.0 + (drift * 0.2), 0.35), 1.0, 3.2), 2),
                "pressure": round(_bounded(random.gauss(5.5, 0.22), 5.0, 6.0), 2),
                "rpm": round(_bounded(random.gauss(3500, 45), 3400, 3600), 2),
                "motor_current": round(_bounded(random.gauss(11.5 + (drift * 0.1), 0.55), 10.0, 13.0), 2),
            }
        )

    return rows


def _generate_warning_rows(machine_id: int, count: int) -> list[dict[str, float | int | datetime]]:
    rows = []
    timestamp = datetime.utcnow() - timedelta(minutes=count)

    temp = 64.0
    vib = 2.2
    current = 12.1
    rpm = 3510.0

    for i in range(count):
        temp += random.uniform(0.04, 0.11)
        vib += random.uniform(0.02, 0.08)
        current += random.uniform(0.01, 0.06)
        rpm += random.uniform(-8, 7)

        rows.append(
            {
                "machine_id": machine_id,
                "timestamp": timestamp + timedelta(minutes=i),
                "temperature": round(_bounded(random.gauss(temp, 1.0), 62, 78), 2),
                "vibration": round(_bounded(random.gauss(vib, 0.4), 1.5, 5.0), 2),
                "pressure": round(_bounded(random.gauss(5.4, 0.3), 4.7, 6.2), 2),
                "rpm": round(_bounded(random.gauss(rpm, 70), 3300, 3620), 2),
                "motor_current": round(_bounded(random.gauss(current, 0.65), 11.0, 16.5), 2),
            }
        )

    return rows


def _generate_failure_rows(machine_id: int, count: int) -> list[dict[str, float | int | datetime]]:
    rows = []
    timestamp = datetime.utcnow() - timedelta(minutes=count)

    temp = 68.0
    vib = 3.0
    current = 13.0
    rpm = 3495.0

    for i in range(count):
        # Correlated degradation: temperature/vibration/current rise while RPM trends down.
        temp += random.uniform(0.10, 0.28)
        vib += random.uniform(0.08, 0.20)
        current += random.uniform(0.06, 0.16)
        rpm -= random.uniform(2.0, 8.0)

        rows.append(
            {
                "machine_id": machine_id,
                "timestamp": timestamp + timedelta(minutes=i),
                "temperature": round(_bounded(random.gauss(temp, 1.3), 66, 95), 2),
                "vibration": round(_bounded(random.gauss(vib, 0.65), 2.5, 9.5), 2),
                "pressure": round(_bounded(random.gauss(5.1, 0.45), 3.8, 6.6), 2),
                "rpm": round(_bounded(random.gauss(rpm, 95), 3000, 3550), 2),
                "motor_current": round(_bounded(random.gauss(current, 0.9), 12.0, 21.0), 2),
            }
        )

    return rows


def main() -> None:
    random.seed(42)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    normal_df = pd.DataFrame(_generate_normal_rows(machine_id=1, count=240))
    warning_df = pd.DataFrame(_generate_warning_rows(machine_id=1, count=240))
    failure_df = pd.DataFrame(_generate_failure_rows(machine_id=1, count=240))

    normal_df.to_csv(OUTPUT_DIR / "normal_sensor_data.csv", index=False)
    warning_df.to_csv(OUTPUT_DIR / "warning_sensor_data.csv", index=False)
    failure_df.to_csv(OUTPUT_DIR / "failure_sensor_data.csv", index=False)

    print("Generated synthetic sensor datasets in", OUTPUT_DIR)


if __name__ == "__main__":
    main()
