from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest


BASE_DIR = Path(__file__).resolve().parents[1]
SENSOR_DIR = BASE_DIR / "data" / "sensors"
MODEL_DIR = BASE_DIR / "data" / "models"
MODEL_PATH = MODEL_DIR / "anomaly_detector.joblib"

FEATURE_COLUMNS = [
    "temperature",
    "vibration",
    "pressure",
    "rpm",
    "motor_current",
]


def main() -> None:
    normal_path = SENSOR_DIR / "normal_sensor_data.csv"
    if not normal_path.exists():
        raise FileNotFoundError(
            f"Missing {normal_path}. Run scripts/generate_sensor_data.py first."
        )

    normal_df = pd.read_csv(normal_path)
    train_df = normal_df[FEATURE_COLUMNS].copy()

    model = IsolationForest(
        n_estimators=200,
        contamination=0.08,
        random_state=42,
    )
    model.fit(train_df)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)

    print(f"Saved trained anomaly model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
