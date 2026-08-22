from __future__ import annotations


def _range_penalty(value: float, good_min: float, good_max: float, warn_delta: float, critical_delta: float) -> int:
    if good_min <= value <= good_max:
        return 0

    if value < good_min:
        distance = good_min - value
    else:
        distance = value - good_max

    if distance <= warn_delta:
        return 8
    if distance <= critical_delta:
        return 18
    return 30


def calculate_health_score(
    temperature: float,
    vibration: float,
    pressure: float,
    rpm: float,
    motor_current: float,
    anomaly_score: float = 0.0
) -> dict[str, int | str]:
    """Engineering indicator only; not a certified safety metric."""
    score = 100

    score -= _range_penalty(temperature, 55.0, 70.0, 5.0, 12.0)
    score -= _range_penalty(vibration, 0.5, 3.0, 1.0, 3.0)
    score -= _range_penalty(pressure, 4.8, 6.2, 0.6, 1.5)
    score -= _range_penalty(rpm, 3400.0, 3600.0, 120.0, 350.0)
    score -= _range_penalty(motor_current, 9.0, 13.0, 1.2, 3.5)

    score -= int(max(0.0, min(1.0, anomaly_score)) * 35)
    score = max(0, min(100, score))

    if score >= 90:
        status = "excellent"
    elif score >= 75:
        status = "good"
    elif score >= 50:
        status = "warning"
    elif score >= 25:
        status = "critical"
    else:
        status = "severe"

    return {
        "health_score": score,
        "health_status": status
    }
