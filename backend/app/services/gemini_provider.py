from __future__ import annotations

from typing import Any

from google import genai

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
        self.model = (model or GEMINI_MODEL or "gemini-1.5-flash").strip()
        self.embedding_model = (embedding_model or GEMINI_EMBEDDING_MODEL or "text-embedding-004").strip()
        self._configured = False
        self._client: genai.Client | None = None

    def _normalize_model_name(self, model_name: str) -> str:
        return model_name.strip().removeprefix("models/").removeprefix("model/")

    def _ensure_configured(self) -> None:
        if not self.api_key:
            raise GeminiProviderError("Gemini API key is not configured")
        if not self._configured:
            self._client = genai.Client(api_key=self.api_key)
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

    def _extract_response_text(self, response: Any) -> str | None:
        if response is None:
            return None
        if isinstance(response, dict):
            text = response.get("text")
            if text:
                return str(text)
            candidates = response.get("candidates") or []
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                content = candidate.get("content") or {}
                parts = content.get("parts") or []
                for part in parts:
                    if isinstance(part, dict) and part.get("text"):
                        return str(part["text"])
            return None

        text = getattr(response, "text", None)
        if text:
            return str(text)

        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content is None:
                continue
            parts = getattr(content, "parts", None) or []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    return str(part_text)
        return None

    def generate_text(self, prompt: str) -> str:
        self._ensure_configured()
        try:
            response = self._client.models.generate_content(
                model=self._normalize_model_name(self.model),
                contents=prompt,
                config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": LLM_MAX_TOKENS,
                },
            )
        except Exception as exc:  # pragma: no cover - exercised via LLMServiceError layer
            logger.exception("Gemini generation failed")
            raise self._normalize_error(exc, "Gemini provider failed to generate a response") from exc

        text = self._extract_response_text(response)
        if text is None:
            raise GeminiProviderError("Gemini returned an empty response")
        stripped = str(text).strip()
        if not stripped:
            raise GeminiProviderError("Gemini returned an empty response")
        return stripped

    def _extract_embedding_values(self, response: Any) -> list[float] | None:
        if response is None:
            return None

        if isinstance(response, dict):
            embeddings = response.get("embeddings") or []
            if embeddings:
                first = embeddings[0]
                values = first.get("values") if isinstance(first, dict) else None
                if values is not None:
                    return [float(value) for value in values]
                weights = first.get("embedding") if isinstance(first, dict) else None
                if weights is not None:
                    return [float(value) for value in weights]
            payload = response.get("embedding")
            if payload is not None:
                return [float(value) for value in payload]
            return None

        embeddings = getattr(response, "embeddings", None) or []
        if embeddings:
            first = embeddings[0]
            values = getattr(first, "values", None)
            if values is not None:
                return [float(value) for value in values]
            payload = getattr(first, "embedding", None)
            if payload is not None:
                return [float(value) for value in payload]

        payload = getattr(response, "embedding", None)
        if payload is not None:
            return [float(value) for value in payload]
        return None

    def embed_text(self, text: str) -> list[float]:
        self._ensure_configured()
        if not text or not text.strip():
            raise GeminiProviderError("Cannot embed empty text.")
        try:
            response = self._client.models.embed_content(
                model=self._normalize_model_name(self.embedding_model),
                contents=text,
                config={"task_type": "retrieval_document"},
            )
        except Exception as exc:  # pragma: no cover - exercised via caller error handling
            logger.exception("Gemini embedding failed")
            raise self._normalize_error(exc, "Gemini embedding failed") from exc

        payload = self._extract_embedding_values(response)
        if payload is None:
            raise GeminiProviderError("Gemini embedding response was empty")
        return payload
