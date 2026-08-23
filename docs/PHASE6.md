# Phase 6 Chat API

The stateless `POST /api/chat` endpoint combines machine data, the latest sensor reading, and the existing Phase 5 `Retriever.search()` results. `chat_service.handle_chat()` builds a bounded grounded prompt and calls the isolated OpenAI-compatible adapter in `app/services/llm_service.py` once for normal requests.

## Configuration

Set `LLM_API_KEY` and optionally `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, and `LLM_TIMEOUT_SECONDS`. Configuration is optional for development; without a key, normal requests return a controlled `503`. No key is returned or logged. See `backend/.env.example`.

## Response behavior

The API returns a structured `MaintenanceAnswer` with an assessment, possible causes, recommended actions, safety considerations, and an insufficient-information flag. Sources are attached by the backend from retrieval metadata, never from model-generated filenames. Empty or weak retrieval evidence returns a deterministic abstention without an LLM call. Retrieval confidence is the highest Qdrant cosine score among returned chunks, and `grounded` means it meets `CHAT_MIN_RETRIEVAL_SCORE`.

The complete internal prompt is not returned publicly. Retrieved document content is bounded by `CHAT_CONTEXT_MAX_CHARS`, and retrieved text is treated as untrusted reference data.

## Flow

```text
User -> POST /api/chat -> Chat Router -> Chat Service
  -> Machine/Sensor Context + Retriever.search()
  -> Prompt Builder -> LLM Service -> Structured Answer
  -> Backend Sources + Grounding Metadata -> API Response
```

Run tests from `backend` with `venv\\Scripts\\python.exe -m pytest tests -q`. The Phase 5 evaluator is `PYTHONPATH=. venv\\Scripts\\python.exe scripts\\evaluate_retrieval.py`.
