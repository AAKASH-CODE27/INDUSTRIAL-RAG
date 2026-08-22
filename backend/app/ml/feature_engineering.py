from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


SENSOR_COLUMNS = [
    "temperature",
    "vibration",
    "pressure",
    "rpm",
    "motor_current"
]


def _safe_std(values: pd.Series) -> float:
    if len(values) <= 1:
        return 0.0
    return float(np.std(values.to_numpy(), ddof=0))


def rolling_mean(values: pd.Series, window: int = 3) -> float:
    if values.empty:
        return 0.0
    return float(values.rolling(window=window, min_periods=1).mean().iloc[-1])


def rate_of_change(values: pd.Series) -> float:
    if len(values) <= 1:
        return 0.0
    return float((values.iloc[-1] - values.iloc[0]) / (len(values) - 1))


def build_sensor_features(df: pd.DataFrame) -> dict[str, float]:
    features: dict[str, float] = {}

    if df.empty:
        return features

    for col in SENSOR_COLUMNS:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            features[f"{col}_mean"] = 0.0
            features[f"{col}_std"] = 0.0
            features[f"{col}_min"] = 0.0
            features[f"{col}_max"] = 0.0
            features[f"{col}_rolling_mean"] = 0.0
            continue

        features[f"{col}_mean"] = float(series.mean())
        features[f"{col}_std"] = _safe_std(series)
        features[f"{col}_min"] = float(series.min())
        features[f"{col}_max"] = float(series.max())
        features[f"{col}_rolling_mean"] = rolling_mean(series)

    # Rate-based features are strongest predictors of rapidly worsening states.
    for col in ["temperature", "vibration", "motor_current"]:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        features[f"{col}_rate"] = rate_of_change(series)

    return features


def dataframe_from_sensor_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=SENSOR_COLUMNS)

    df = pd.DataFrame(records)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp")

    for col in SENSOR_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=SENSOR_COLUMNS)
