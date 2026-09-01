from __future__ import annotations

from typing import Any

import google.generativeai as genai

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    GEMINI_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GeminiProviderError(Exception):
    """Raised when the configured Gemini provider cannot complete a request."""


class GeminiProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None, embedding_model: str | None = None):
        self.api_key = (api_key or GEMINI_API_KEY or "").strip()
        self.model = model or GEMINI_MODEL
        self.embedding_model = embedding_model or GEMINI_EMBEDDING_MODEL
        self._configured = False

    def _ensure_configured(self) -> None:
        if not self.api_key:
            raise GeminiProviderError("Gemini API key is not configured")
        if not self._configured:
            genai.configure(api_key=self.api_key)
            self._configured = True

    def _normalize_error(self, exc: Exception, fallback: str) -> GeminiProviderError:
        message = str(exc).lower()
        if "quota" in message or "rate limit" in message or "429" in message:
            return GeminiProviderError("Gemini rate limit exceeded")
        if "timeout" in message or "timed out" in message or "deadline" in message:
            return GeminiProviderError("Gemini request timed out")
        if "api key" in message or "authentication" in message or "forbidden" in message or "401" in message:
            return GeminiProviderError("Gemini API key is invalid")
        if "not found" in message or "unsupported" in message or "invalid" in message:
            return GeminiProviderError(fallback)
        if "unavailable" in message or "service" in message or "connection" in message:
            return GeminiProviderError("Gemini provider is temporarily unavailable")
        return GeminiProviderError(fallback)

    def generate_text(self, prompt: str) -> str:
        self._ensure_configured()
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": LLM_MAX_TOKENS,
                },
            )
        except Exception as exc:  # pragma: no cover - exercised via LLMServiceError layer
            logger.exception("Gemini generation failed")
            raise self._normalize_error(exc, "Gemini provider failed to generate a response") from exc

        text = getattr(response, "text", None)
        if text is None:
            raise GeminiProviderError("Gemini returned an empty response")
        stripped = str(text).strip()
        if not stripped:
            raise GeminiProviderError("Gemini returned an empty response")
        return stripped

    def embed_text(self, text: str) -> list[float]:
        self._ensure_configured()
        if not text or not text.strip():
            raise GeminiProviderError("Cannot embed empty text.")
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document",
            )
        except Exception as exc:  # pragma: no cover - exercised via caller error handling
            logger.exception("Gemini embedding failed")
            raise self._normalize_error(exc, "Gemini embedding failed") from exc

        payload = result.get("embedding") if isinstance(result, dict) else getattr(result, "embedding", None)
        if payload is None:
            raise GeminiProviderError("Gemini embedding response was empty")
        return [float(value) for value in payload]
