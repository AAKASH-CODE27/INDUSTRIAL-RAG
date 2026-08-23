from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request

from app.core.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MAX_RETRIES,
    LLM_RETRY_DELAY_SECONDS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
)
from app.models.chat_schemas import MaintenanceAnswer
from app.core.logging_config import get_logger


class LLMServiceError(Exception):
    """Raised when the configured LLM cannot return a valid answer."""


logger = get_logger(__name__)
TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}


def generate(prompt: str) -> MaintenanceAnswer:
    if not LLM_API_KEY:
        raise LLMServiceError("LLM provider is not configured")

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an Industrial Maintenance AI Assistant. "
                    "Return ONLY valid JSON. "
                    "The JSON must contain exactly these fields: "
                    "assessment, possible_causes, recommended_actions, "
                    "safety_considerations, insufficient_information. "
                    "Do not use markdown or code fences. "
                    "Use only the information supplied in the prompt. "
                    "Never invent measurements, causes, procedures, or facts. "
                    "If the information is insufficient, set "
                    "insufficient_information to true."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
    }

    request = urllib.request.Request(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    response_data = None
    max_attempts = 1 + min(1, max(0, LLM_MAX_RETRIES))
    started_at = time.perf_counter()
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(
                request,
                timeout=LLM_TIMEOUT_SECONDS,
            ) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code in TRANSIENT_HTTP_STATUSES and attempt < max_attempts:
                logger.warning(
                    "LLM transient failure, retrying attempt %s/%s: status=%s model=%s elapsed_ms=%.1f",
                    attempt + 1,
                    max_attempts,
                    exc.code,
                    LLM_MODEL,
                    (time.perf_counter() - started_at) * 1000,
                )
                time.sleep(max(0, LLM_RETRY_DELAY_SECONDS) * (2 ** (attempt - 1)))
                continue
            logger.error(
                "LLM generation failed after retry: status=%s model=%s attempt=%s elapsed_ms=%.1f",
                exc.code,
                LLM_MODEL,
                attempt,
                (time.perf_counter() - started_at) * 1000,
            )
            raise LLMServiceError(f"LLM provider returned HTTP {exc.code}") from exc

        except urllib.error.URLError as exc:
            is_connection_reset = isinstance(exc.reason, ConnectionResetError)
            if attempt < max_attempts and (is_connection_reset or isinstance(exc.reason, OSError)):
                logger.warning(
                    "LLM transient failure, retrying attempt %s/%s: connection model=%s elapsed_ms=%.1f",
                    attempt + 1,
                    max_attempts,
                    LLM_MODEL,
                    (time.perf_counter() - started_at) * 1000,
                )
                time.sleep(max(0, LLM_RETRY_DELAY_SECONDS) * (2 ** (attempt - 1)))
                continue
            logger.error(
                "LLM generation failed after retry: connection model=%s attempt=%s elapsed_ms=%.1f",
                LLM_MODEL,
                attempt,
                (time.perf_counter() - started_at) * 1000,
            )
            raise LLMServiceError("Unable to connect to the LLM provider") from exc

        except (TimeoutError, socket.timeout) as exc:
            if attempt < max_attempts:
                logger.warning(
                    "LLM transient failure, retrying attempt %s/%s: timeout model=%s elapsed_ms=%.1f",
                    attempt + 1,
                    max_attempts,
                    LLM_MODEL,
                    (time.perf_counter() - started_at) * 1000,
                )
                time.sleep(max(0, LLM_RETRY_DELAY_SECONDS) * (2 ** (attempt - 1)))
                continue
            logger.error(
                "LLM generation failed after retry: timeout model=%s attempt=%s elapsed_ms=%.1f",
                LLM_MODEL,
                attempt,
                (time.perf_counter() - started_at) * 1000,
            )
            raise LLMServiceError("LLM provider request timed out") from exc

        except json.JSONDecodeError as exc:
            raise LLMServiceError("LLM provider returned invalid JSON") from exc

    try:
        content = response_data["choices"][0]["message"]["content"]

        if not content:
            raise LLMServiceError("LLM provider returned an empty response")

        content = content.strip()

        # Remove accidental markdown fences.
        if content.startswith("```json"):
            content = content[len("```json"):].strip()
        elif content.startswith("```"):
            content = content[len("```"):].strip()

        if content.endswith("```"):
            content = content[:-3].strip()

        parsed = json.loads(content)

        answer = MaintenanceAnswer.model_validate(parsed)
        logger.info(
            "LLM generation succeeded: model=%s attempt=%s elapsed_ms=%.1f",
            LLM_MODEL,
            attempt,
            (time.perf_counter() - started_at) * 1000,
        )
        return answer

    except json.JSONDecodeError as exc:
        logger.error(
            "LLM generation failed after retry: invalid_json model=%s attempt=%s elapsed_ms=%.1f",
            LLM_MODEL,
            attempt,
            (time.perf_counter() - started_at) * 1000,
        )
        raise LLMServiceError("LLM provider returned non-JSON content") from exc

    except (KeyError, IndexError, TypeError) as exc:
        logger.error(
            "LLM generation failed after retry: invalid_response model=%s attempt=%s elapsed_ms=%.1f",
            LLM_MODEL,
            attempt,
            (time.perf_counter() - started_at) * 1000,
        )
        raise LLMServiceError("LLM provider returned an unexpected response") from exc

    except ValueError as exc:
        logger.error(
            "LLM generation failed after retry: schema_validation model=%s attempt=%s elapsed_ms=%.1f",
            LLM_MODEL,
            attempt,
            (time.perf_counter() - started_at) * 1000,
        )
        raise LLMServiceError("LLM provider response failed validation") from exc
    