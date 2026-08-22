from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.logging_config import get_logger
from app.ml.feature_engineering import build_sensor_features


logger = get_logger(__name__)


class SensorAnomalyDetector:
    def __init__(self) -> None:
        self.model = None
        self.model_feature_columns: list[str] | None = None
        self._load_model()

    def _load_model(self) -> None:
        model_path = Path(__file__).resolve().parents[2] / "data" / "models" / "anomaly_detector.joblib"

        if not model_path.exists():
            logger.info("No trained anomaly model found at %s. Rule-based detection only.", model_path)
            return

        try:
            loaded = joblib.load(model_path)
            if isinstance(loaded, dict) and "model" in loaded:
                self.model = loaded["model"]
                self.model_feature_columns = loaded.get("feature_columns")
            else:
                self.model = loaded
            logger.info("Anomaly model loaded from %s", model_path)
        except Exception as exc:
            logger.exception("Failed to load anomaly model. Falling back to rules only: %s", exc)

    def _rule_based_detection(self, df: pd.DataFrame) -> dict[str, object]:
        reasons: list[str] = []
        score = 0.0

        latest = df.iloc[-1]
        temp = float(latest["temperature"])
        vib = float(latest["vibration"])
        pressure = float(latest["pressure"])
        rpm = float(latest["rpm"])
        current = float(latest["motor_current"])

        if temp >= 75:
            reasons.append("High temperature")
            score += 0.15
        if temp >= 85:
            reasons.append("Critical temperature")
            score += 0.25

        if vib >= 4.0:
            reasons.append("High vibration")
            score += 0.20
        if vib >= 7.0:
            reasons.append("Critical vibration")
            score += 0.25

        if pressure < 4.5 or pressure > 6.5:
            reasons.append("Abnormal pressure")
            score += 0.12

        if rpm < 3300:
            reasons.append("Low RPM")
            score += 0.15

        if current >= 15:
            reasons.append("High motor current")
            score += 0.18

        if len(df) >= 4:
            temp_rate = (float(df["temperature"].iloc[-1]) - float(df["temperature"].iloc[-4])) / 3.0
            vib_rate = (float(df["vibration"].iloc[-1]) - float(df["vibration"].iloc[-4])) / 3.0
            if temp_rate >= 1.5:
                reasons.append("Rapid temperature increase")
                score += 0.20
            if vib_rate >= 0.8:
                reasons.append("Rapid vibration increase")
                score += 0.20

        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            severity = "high"
        elif score >= 0.45:
            severity = "medium"
        elif score >= 0.2:
            severity = "low"
        else:
            severity = "normal"

        return {
            "is_anomaly": score >= 0.2,
            "anomaly_score": round(score, 3),
            "severity": severity,
            "reasons": reasons
        }

    def _model_score(self, df: pd.DataFrame, features: dict[str, float]) -> tuple[bool, float] | None:
        if self.model is None:
            return None

        try:
            if self.model_feature_columns:
                vector = [float(features.get(col, 0.0)) for col in self.model_feature_columns]
            else:
                vector = [
                    float(df.iloc[-1]["temperature"]),
                    float(df.iloc[-1]["vibration"]),
                    float(df.iloc[-1]["pressure"]),
                    float(df.iloc[-1]["rpm"]),
                    float(df.iloc[-1]["motor_current"]),
                ]

            prediction = int(self.model.predict([vector])[0])
            decision = float(self.model.decision_function([vector])[0])

            # Convert decision function into [0, 1] risk proxy.
            normalized = 1.0 / (1.0 + np.exp(3.0 * decision))
            return prediction == -1, float(normalized)
        except Exception as exc:
            logger.exception("Anomaly model inference failed: %s", exc)
            return None

    def analyze(self, df: pd.DataFrame) -> dict[str, object]:
        if df.empty:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "severity": "normal",
                "reasons": ["No sensor data available"]
            }

        features = build_sensor_features(df)
        rule_result = self._rule_based_detection(df)
        model_result = self._model_score(df, features)

        if model_result is None:
            return rule_result

        model_is_anomaly, model_score = model_result
        final_score = float(np.clip((rule_result["anomaly_score"] * 0.65) + (model_score * 0.35), 0.0, 1.0))

        reasons = list(rule_result["reasons"])
        if model_is_anomaly:
            reasons.append("IsolationForest anomaly pattern")

        if final_score >= 0.75:
            severity = "high"
        elif final_score >= 0.45:
            severity = "medium"
        elif final_score >= 0.2:
            severity = "low"
        else:
            severity = "normal"

        return {
            "is_anomaly": final_score >= 0.2 or model_is_anomaly,
            "anomaly_score": round(final_score, 3),
            "severity": severity,
            "reasons": reasons
        }
