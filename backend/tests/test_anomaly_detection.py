from datetime import datetime, timedelta

from app.ml.health_score import calculate_health_score


def _create_machine(client, code: str = "CNC-001") -> int:
    response = client.post(
        "/api/machines",
        json={
            "machine_code": code,
            "name": "CNC Milling Machine",
            "machine_type": "CNC",
            "location": "Production Floor A",
            "status": "active",
        },
    )
    return response.json()["id"]


def _post_reading(client, machine_id: int, minute_offset: int, t: float, v: float, p: float, rpm: float, c: float):
    ts = (datetime.utcnow() + timedelta(minutes=minute_offset)).isoformat()
    return client.post(
        "/api/sensors",
        json={
            "machine_id": machine_id,
            "timestamp": ts,
            "temperature": t,
            "vibration": v,
            "pressure": p,
            "rpm": rpm,
            "motor_current": c,
        },
    )


def test_health_score_ranges():
    normal = calculate_health_score(62, 2.0, 5.5, 3500, 11.5, 0.05)
    abnormal = calculate_health_score(88, 7.8, 4.0, 3200, 18.0, 0.9)

    assert normal["health_score"] > abnormal["health_score"]
    assert normal["health_status"] in {"excellent", "good"}
    assert abnormal["health_status"] in {"warning", "critical", "severe"}


def test_anomaly_detection_normal_data(client):
    machine_id = _create_machine(client)

    for i in range(8):
        response = _post_reading(client, machine_id, i, 62 + (i * 0.1), 2.0 + (i * 0.05), 5.6, 3500, 11.8)
        assert response.status_code == 201

    result = client.post(f"/api/anomaly/analyze/{machine_id}")
    assert result.status_code == 200
    payload = result.json()
    assert payload["anomaly_score"] < 0.45


def test_anomaly_detection_abnormal_data(client):
    machine_id = _create_machine(client)

    values = [
        (62, 2.1, 5.6, 3500, 12.2),
        (63, 2.4, 5.6, 3490, 12.5),
        (65, 3.2, 5.4, 3480, 13.4),
        (69, 4.8, 5.2, 3450, 14.8),
        (74, 6.5, 4.9, 3380, 16.1),
        (80, 8.1, 4.5, 3200, 18.2),
    ]

    for i, (t, v, p, rpm, c) in enumerate(values):
        response = _post_reading(client, machine_id, i, t, v, p, rpm, c)
        assert response.status_code == 201

    result = client.post(f"/api/anomaly/analyze/{machine_id}")
    assert result.status_code == 200
    payload = result.json()

    assert payload["is_anomaly"] is True
    assert payload["anomaly_score"] >= 0.45
    assert payload["health_status"] in {"warning", "critical", "severe"}


def test_machine_health_and_overview(client):
    machine_id = _create_machine(client)

    for i in range(3):
        _post_reading(client, machine_id, i, 62, 2.2, 5.6, 3500, 12.1)

    health_response = client.get(f"/api/machines/{machine_id}/health")
    assert health_response.status_code == 200

    overview_response = client.get(f"/api/machines/{machine_id}/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["machine"]["id"] == machine_id
    assert "health" in overview


def test_end_to_end_demonstration_flow(client):
    machine_id = _create_machine(client, code="CNC-001")

    # Insert readings with progression from normal to failure-like behavior.
    progression = [
        (62.0, 2.1, 5.8, 3500, 12.2),
        (63.0, 2.4, 5.7, 3490, 12.5),
        (65.0, 3.2, 5.6, 3480, 13.4),
        (69.0, 4.8, 5.3, 3450, 14.8),
        (74.0, 6.5, 5.0, 3380, 16.1),
        (80.0, 8.1, 4.5, 3200, 18.2),
    ]

    for i, (t, v, p, rpm, c) in enumerate(progression):
        response = _post_reading(client, machine_id, i, t, v, p, rpm, c)
        assert response.status_code == 201

    anomaly_response = client.post(f"/api/anomaly/analyze/{machine_id}")
    assert anomaly_response.status_code == 200
    anomaly_payload = anomaly_response.json()
    assert anomaly_payload["is_anomaly"] is True

    failure_response = client.post(
        "/api/failures",
        json={
            "machine_id": machine_id,
            "failure_code": "E104",
            "failure_type": "Spindle vibration",
            "severity": "High",
            "symptoms": "High vibration, temperature increase",
            "root_cause": "Spindle bearing degradation",
            "resolution": "Replace bearing and check alignment",
            "downtime_minutes": 145,
            "occurred_at": datetime.utcnow().isoformat(),
        },
    )
    assert failure_response.status_code == 201

    maintenance_response = client.post(
        "/api/maintenance",
        json={
            "machine_id": machine_id,
            "maintenance_type": "corrective",
            "description": "Spindle inspection",
            "findings": "Excessive bearing wear",
            "action_taken": "Bearing replaced and shaft aligned",
            "parts_replaced": "Spindle bearing",
            "technician": "Technician-01",
            "cost": 720.0,
            "downtime_minutes": 120,
            "performed_at": datetime.utcnow().isoformat(),
        },
    )
    assert maintenance_response.status_code == 201

    overview_response = client.get(f"/api/machines/{machine_id}/overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["machine"]["machine_code"] == "CNC-001"
    assert len(overview_payload["recent_sensor_readings"]) >= 1
    assert len(overview_payload["recent_failures"]) >= 1
    assert len(overview_payload["recent_maintenance"]) >= 1
