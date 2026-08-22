def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_db_connection(client):
    response = client.get("/api/db-test")
    assert response.status_code == 200
    payload = response.json()
    assert payload["database"] == "connected"
    assert payload["test_result"] == 1
