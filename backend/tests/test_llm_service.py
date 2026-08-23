import json
import urllib.error

import pytest

from app.models.chat_schemas import MaintenanceAnswer
from app.services import llm_service


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def valid_provider_response():
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        MaintenanceAnswer(
                            assessment="OK",
                            possible_causes=[],
                            recommended_actions=[],
                            safety_considerations=[],
                            insufficient_information=False,
                        ).model_dump()
                    )
                }
            }
        ]
    }


def http_error(status):
    return urllib.error.HTTPError("https://provider.test", status, "provider error", {}, None)


def test_generate_retries_transient_failure_once(monkeypatch):
    calls = []
    sleeps = []
    responses = [http_error(503), FakeResponse(valid_provider_response())]

    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service, "LLM_RETRY_DELAY_SECONDS", 1)

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(llm_service.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(llm_service.time, "sleep", sleeps.append)

    answer = llm_service.generate("test prompt")

    assert answer.assessment == "OK"
    assert len(calls) == 2
    assert sleeps == [1]


def test_generate_does_not_retry_permanent_http_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service.urllib.request, "urlopen", lambda request, timeout: calls.append(1) or (_ for _ in ()).throw(http_error(401)))

    with pytest.raises(llm_service.LLMServiceError, match="HTTP 401"):
        llm_service.generate("test prompt")

    assert len(calls) == 1


def test_generate_does_not_retry_invalid_json(monkeypatch):
    calls = []
    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service.urllib.request, "urlopen", lambda request, timeout: calls.append(1) or FakeResponse({"choices": [{"message": {"content": "not json"}}]}))

    with pytest.raises(llm_service.LLMServiceError, match="non-JSON"):
        llm_service.generate("test prompt")

    assert len(calls) == 1
