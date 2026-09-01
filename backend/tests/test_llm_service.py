import json
from unittest.mock import MagicMock

import pytest

from app.models.chat_schemas import MaintenanceAnswer
from app.services import llm_service
from app.services.gemini_provider import GeminiProviderError


def valid_answer():
    return MaintenanceAnswer(
        assessment="OK",
        possible_causes=[],
        recommended_actions=[],
        safety_considerations=[],
        insufficient_information=False,
    )


def test_generate_retries_transient_failure_once(monkeypatch):
    call_count = [0]
    sleeps = []

    def fake_generate_text(self, prompt):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call fails with rate limit (transient)
            raise GeminiProviderError("Gemini rate limit exceeded")
        # Second call succeeds
        return json.dumps(valid_answer().model_dump())

    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service, "LLM_RETRY_DELAY_SECONDS", 0.01)
    monkeypatch.setattr(llm_service.GeminiProvider, "generate_text", fake_generate_text)
    monkeypatch.setattr(llm_service.time, "sleep", sleeps.append)

    answer = llm_service.generate("test prompt")

    assert answer.assessment == "OK"
    assert call_count[0] == 2
    assert len(sleeps) == 1


def test_generate_does_not_retry_permanent_http_failure(monkeypatch):
    def fake_generate_text(self, prompt):
        raise GeminiProviderError("Gemini API key is invalid")

    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service.GeminiProvider, "generate_text", fake_generate_text)

    with pytest.raises(llm_service.LLMServiceError, match="invalid"):
        llm_service.generate("test prompt")


def test_generate_does_not_retry_invalid_json(monkeypatch):
    def fake_generate_text(self, prompt):
        return "not valid json {{"

    monkeypatch.setattr(llm_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_service, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(llm_service.GeminiProvider, "generate_text", fake_generate_text)

    with pytest.raises(llm_service.LLMServiceError, match="non-JSON"):
        llm_service.generate("test prompt")
