from datetime import datetime, timedelta


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


def test_sensor_creation_and_invalid_machine(client):
    machine_id = _create_machine(client)

    create_response = client.post(
        "/api/sensors",
        json={
            "machine_id": machine_id,
            "temperature": 62.4,
            "vibration": 2.1,
            "pressure": 5.6,
            "rpm": 3520,
            "motor_current": 12.2,
        },
    )
    assert create_response.status_code == 201

    invalid_response = client.post(
        "/api/sensors",
        json={
            "machine_id": 999,
            "temperature": 62.4,
            "vibration": 2.1,
            "pressure": 5.6,
            "rpm": 3520,
            "motor_current": 12.2,
        },
    )
    assert invalid_response.status_code == 404


def test_sensor_history_and_summary(client):
    machine_id = _create_machine(client)
    base_time = datetime.utcnow() - timedelta(minutes=10)

    for i in range(5):
        response = client.post(
            "/api/sensors",
            json={
                "machine_id": machine_id,
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "temperature": 60 + i,
                "vibration": 2 + (i * 0.2),
                "pressure": 5.5,
                "rpm": 3500 - (i * 5),
                "motor_current": 11 + (i * 0.1),
            },
        )
        assert response.status_code == 201

    history = client.get(f"/api/sensors/machine/{machine_id}/history", params={"limit": 3})
    assert history.status_code == 200
    assert len(history.json()) == 3

    summary = client.get(f"/api/sensors/machine/{machine_id}/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["reading_count"] == 5
    assert payload["temperature"]["max"] >= payload["temperature"]["min"]


def test_bulk_sensor_insertion(client):
    machine_id = _create_machine(client)

    payload = {
        "readings": [
            {
                "machine_id": machine_id,
                "temperature": 63.0,
                "vibration": 2.4,
                "pressure": 5.6,
                "rpm": 3490,
                "motor_current": 12.3,
            },
            {
                "machine_id": machine_id,
                "temperature": 63.2,
                "vibration": 2.5,
                "pressure": 5.7,
                "rpm": 3488,
                "motor_current": 12.4,
            },
        ]
    }

    response = client.post("/api/sensors/bulk", json=payload)
    assert response.status_code == 201
    assert response.json()["inserted"] == 2


def test_csv_validation(client):
    _create_machine(client)

    bad_csv = "machine_id,timestamp,temperature\n1,2026-01-01T10:00:00,60.1\n"

    response = client.post(
        "/api/sensors/upload-csv",
        files={"file": ("bad.csv", bad_csv, "text/csv")},
    )
    assert response.status_code == 400
