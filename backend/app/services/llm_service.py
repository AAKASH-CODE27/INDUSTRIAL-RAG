from __future__ import annotations

import json
import time

from app.core.config import (
    GEMINI_API_KEY,
    LLM_MAX_RETRIES,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_RETRY_DELAY_SECONDS,
    LLM_TEMPERATURE,
)
from app.core.logging_config import get_logger
from app.models.chat_schemas import MaintenanceAnswer
from app.services.gemini_provider import GeminiProvider, GeminiProviderError


class LLMServiceError(Exception):
    """Raised when the configured LLM cannot return a valid answer."""


logger = get_logger(__name__)

LLM_API_KEY = GEMINI_API_KEY
LLM_BASE_URL = "https://generativelanguage.googleapis.com"
LLM_TIMEOUT_SECONDS = 30


def generate(prompt: str) -> MaintenanceAnswer:
    key = LLM_API_KEY or GEMINI_API_KEY
    if not key:
        raise LLMServiceError("Gemini API key is not configured")

    provider = GeminiProvider(api_key=key, model=LLM_MODEL)
    attempts = max(1, int(LLM_MAX_RETRIES) + 1)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            content = provider.generate_text(prompt)
            break
        except GeminiProviderError as exc:
            last_error = exc
            if "rate limit" in str(exc).lower() or "timed out" in str(exc).lower():
                if attempt < attempts:
                    logger.warning("Gemini transient failure, retrying attempt %s/%s: %s", attempt + 1, attempts, exc)
                    time.sleep(max(0.0, float(LLM_RETRY_DELAY_SECONDS)) * (2 ** (attempt - 1)))
                    continue
            raise LLMServiceError(str(exc)) from exc
    else:
        if last_error is not None:
            raise LLMServiceError(str(last_error))
        raise LLMServiceError("Gemini provider failed to generate a response")

    try:
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        parsed = json.loads(cleaned)
        answer = MaintenanceAnswer.model_validate(parsed)
        logger.info("Gemini generation succeeded: model=%s", LLM_MODEL)
        return answer
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned non-JSON content: model=%s", LLM_MODEL)
        raise LLMServiceError("Gemini provider returned non-JSON content") from exc
    except ValueError as exc:
        logger.error("Gemini response failed validation: model=%s", LLM_MODEL)
        raise LLMServiceError("Gemini provider response failed validation") from exc
    