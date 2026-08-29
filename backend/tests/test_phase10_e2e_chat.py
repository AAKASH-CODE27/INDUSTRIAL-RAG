from datetime import datetime

from app.core.database import SessionLocal
from app.models.machine import Machine
from app.models.sensor import SensorReading


def create_machine() -> Machine:
    db = SessionLocal()
    machine = Machine(
        machine_code="E2E-CHAT",
        name="End-to-End Motor",
        machine_type="Motor",
        location="Plant C",
        status="active",
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    db.close()
    return machine


def test_end_to_end_chat_flow_uses_provider_and_sources(client, monkeypatch):
    machine = create_machine()
    db = SessionLocal()
    db.add(
        SensorReading(
            machine_id=machine.id,
            timestamp=datetime(2026, 8, 23, 10, 0),
            temperature=78.2,
            vibration=4.1,
            pressure=101.3,
            rpm=1500,
            motor_current=9.2,
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(
        "app.services.retrieval_service.retriever.search",
        lambda query, top_k: [{
            "score": 0.93,
            "text": "High vibration often indicates bearing wear or misalignment.",
            "chunk_id": "chunk-7",
            "document_id": "manual-17",
            "document_name": "Bearing Maintenance Manual",
            "document_type": "manual",
            "machine_type": "Motor",
            "section": "Vibration",
            "page": 14,
            "source": "bearing_manual.pdf",
        }],
    )

    def fake_generate(prompt):
        assert "Why is the vibration high?" in prompt
        assert "Bearing Maintenance Manual" in prompt
        from app.models.chat_schemas import MaintenanceAnswer
        return MaintenanceAnswer(
            assessment="Bearing wear is the likely cause based on the retrieved maintenance guidance.",
            possible_causes=["Bearing wear", "Misalignment"],
            recommended_actions=["Inspect alignment and bearing condition."],
            safety_considerations=["Use lockout/tagout before inspection."],
        )

    monkeypatch.setattr("app.services.llm_service.generate", fake_generate)

    response = client.post(
        "/api/chat",
        json={"machine_id": machine.id, "message": "Why is the vibration high?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is True
    assert payload["retrieval_confidence"] == 0.93
    assert payload["question"] == "Why is the vibration high?"
    assert payload["machine_context"]["machine_code"] == "E2E-CHAT"
    assert payload["sensor_context"]["vibration"] == 4.1
    assert payload["sources"][0]["document_name"] == "Bearing Maintenance Manual"
    assert payload["answer"]["possible_causes"] == ["Bearing wear", "Misalignment"]
