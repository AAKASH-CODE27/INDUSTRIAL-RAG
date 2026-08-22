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


def test_maintenance_crud(client):
    machine_id = _create_machine(client)

    payload = {
        "machine_id": machine_id,
        "maintenance_type": "corrective",
        "description": "Spindle inspection",
        "findings": "Excessive bearing wear",
        "action_taken": "Bearing replaced",
        "parts_replaced": "Spindle bearing",
        "technician": "Technician-01",
        "cost": 450.0,
        "downtime_minutes": 85,
        "performed_at": datetime.utcnow().isoformat(),
    }

    create_response = client.post("/api/maintenance", json=payload)
    assert create_response.status_code == 201
    maintenance_id = create_response.json()["id"]

    get_response = client.get(f"/api/maintenance/{maintenance_id}")
    assert get_response.status_code == 200

    list_response = client.get("/api/maintenance", params={"maintenance_type": "corrective"})
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    update_response = client.put(
        f"/api/maintenance/{maintenance_id}",
        json={"cost": 500.0},
    )
    assert update_response.status_code == 200
    assert float(update_response.json()["cost"]) == 500.0

    delete_response = client.delete(f"/api/maintenance/{maintenance_id}")
    assert delete_response.status_code == 200
