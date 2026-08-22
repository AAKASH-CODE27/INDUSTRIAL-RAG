from datetime import datetime


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


def test_failure_crud(client):
    machine_id = _create_machine(client)

    payload = {
        "machine_id": machine_id,
        "failure_code": "E104",
        "failure_type": "Spindle vibration",
        "severity": "High",
        "symptoms": "High vibration, temperature increase",
        "root_cause": "Spindle bearing degradation",
        "resolution": "Replace bearing and check alignment",
        "downtime_minutes": 120,
        "occurred_at": datetime.utcnow().isoformat(),
    }

    create_response = client.post("/api/failures", json=payload)
    assert create_response.status_code == 201
    failure_id = create_response.json()["id"]

    get_response = client.get(f"/api/failures/{failure_id}")
    assert get_response.status_code == 200

    search_response = client.get("/api/failures/search", params={"failure_code": "E104"})
    assert search_response.status_code == 200
    assert len(search_response.json()) >= 1

    update_response = client.put(
        f"/api/failures/{failure_id}",
        json={"severity": "Critical"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["severity"] == "Critical"

    delete_response = client.delete(f"/api/failures/{failure_id}")
    assert delete_response.status_code == 200
