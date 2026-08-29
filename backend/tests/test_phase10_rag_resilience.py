import socket

from app.core.database import SessionLocal
from app.models.machine import Machine
from app.services import llm_service


def create_machine() -> Machine:
    db = SessionLocal()
    machine = Machine(
        machine_code="RAG-10",
        name="RAG Resilience Motor",
        machine_type="Motor",
        location="Plant B",
        status="active",
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    db.close()
    return machine


def test_rag_search_handles_retriever_failure(client, monkeypatch):
    def boom(query, top_k):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr("app.api.rag.retriever.search", boom)

    response = client.post("/api/rag/search", json={"query": "high vibration", "top_k": 5})

    assert response.status_code == 500
    assert "Retrieval failed" in response.json()["detail"]


def test_chat_abstains_on_low_confidence_retrieval(client, monkeypatch):
    machine = create_machine()
    monkeypatch.setattr(
        "app.services.retrieval_service.retriever.search",
        lambda query, top_k: [{"text": "Weak evidence", "score": 0.08, "source": "weak.txt"}],
    )
    llm_calls = []
    monkeypatch.setattr("app.services.llm_service.generate", lambda prompt: llm_calls.append(prompt) or None)

    response = client.post(
        "/api/chat",
        json={"machine_id": machine.id, "message": "Why is the vibration high?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is False
    assert payload["answer"]["insufficient_information"] is True
    assert llm_calls == []


def test_chat_skips_malformed_retrieval_results(client, monkeypatch):
    machine = create_machine()
    monkeypatch.setattr(
        "app.services.retrieval_service.retriever.search",
        lambda query, top_k: ["malformed", {"text": "valid text", "score": 0.55, "source": "case.txt"}],
    )
    llm_calls = []
    monkeypatch.setattr("app.services.llm_service.generate", lambda prompt: llm_calls.append(prompt) or None)

    response = client.post(
        "/api/chat",
        json={"machine_id": machine.id, "message": "What is causing this issue?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]["insufficient_information"] is True
    assert payload["sources"] == []
    assert llm_calls == []


def test_chat_rejects_empty_and_extremely_long_question(client):
    machine = create_machine()

    empty = client.post("/api/chat", json={"machine_id": machine.id, "message": "   "})
    long_question = "x" * 5000
    long_response = client.post("/api/chat", json={"machine_id": machine.id, "message": long_question})

    assert empty.status_code == 422
    assert long_response.status_code == 422


def test_rag_api_handles_empty_query(client):
    response = client.post("/api/rag/search", json={"query": "", "top_k": 3})
    assert response.status_code == 422


def test_llm_generate_requires_configuration(monkeypatch):
    monkeypatch.setattr(llm_service, "LLM_API_KEY", "")

    try:
        llm_service.generate("test prompt")
    except llm_service.LLMServiceError as exc:
        assert "not configured" in str(exc).lower()
    else:
        raise AssertionError("Expected LLMServiceError when provider is not configured")


def test_llm_generate_handles_timeout(monkeypatch):
    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service, "LLM_RETRY_DELAY_SECONDS", 0)
    monkeypatch.setattr(llm_service.urllib.request, "urlopen", lambda request, timeout: (_ for _ in ()).throw(socket.timeout()))

    try:
        llm_service.generate("test prompt")
    except llm_service.LLMServiceError as exc:
        assert "timed out" in str(exc).lower()
    else:
        raise AssertionError("Expected LLMServiceError when provider times out")
