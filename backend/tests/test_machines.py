def _create_machine(client, code: str = "CNC-001"):
    return client.post(
        "/api/machines",
        json={
            "machine_code": code,
            "name": "CNC Milling Machine",
            "machine_type": "CNC",
            "location": "Production Floor A",
            "status": "active",
        },
    )


def test_machine_crud(client):
    create_response = _create_machine(client)
    assert create_response.status_code == 201
    machine = create_response.json()
    machine_id = machine["id"]

    list_response = client.get("/api/machines")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/machines/{machine_id}")
    assert get_response.status_code == 200

    update_response = client.put(
        f"/api/machines/{machine_id}",
        json={"location": "Production Floor B", "status": "maintenance"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "maintenance"

    delete_response = client.delete(f"/api/machines/{machine_id}")
    assert delete_response.status_code == 200


def test_duplicate_machine_code(client):
    assert _create_machine(client, code="CNC-001").status_code == 201
    duplicate_response = _create_machine(client, code="CNC-001")
    assert duplicate_response.status_code == 400


def test_machine_not_found(client):
    response = client.get("/api/machines/9999")
    assert response.status_code == 404
