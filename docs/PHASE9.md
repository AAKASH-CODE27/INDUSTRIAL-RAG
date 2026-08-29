# Phase 9: Industrial Maintenance Chat UI

## Objective

Phase 9 adds the technician-facing application layer around the existing Phase
8 RAG backend. The frontend is intentionally framework-free because the
repository had an empty `frontend/` directory and no frontend build or test
configuration.

## Architecture

```text
Browser at /app
  -> GET /api/machines
  -> POST /api/chat
  -> Phase 8 ChatService
  -> existing Retriever / Qdrant / LLM adapter
  -> structured answer + verified sources
```

The browser does not perform embeddings, vector search, prompting, ranking, or
LLM calls. The backend remains the source of truth for machines, evidence,
grounding, and answer generation.

## Interface

Open `/app` after starting the backend. The console provides:

- machine selector populated from `GET /api/machines`
- selected machine code, name, type, location, and status
- maintenance question composer with submit/loading states
- readable technician and assistant messages
- grounded versus insufficient-evidence answer styling
- source/evidence rail showing only metadata returned by the backend
- clear conversation control
- friendly validation, 404, backend, timeout, and network errors

The chat request uses the existing contract:

```json
{
  "machine_id": 1,
  "question": "Why is the vibration high?",
  "top_k": 5
}
```

## Grounding UX

The UI displays `insufficient_information` as an uncertainty state and never
creates sources or confidence values itself. Document and sensor grounding
rules remain implemented by Phase 8 on the backend.

## Manual verification

1. From `backend`, start `uvicorn app.main:app --reload`.
2. Open `http://127.0.0.1:8000/app`.
3. Confirm the machine register loads and select a machine.
4. Ask a known maintenance question such as `Why is the vibration high?`.
5. Confirm the answer and evidence metadata appear.
6. Ask `What are the latest sensor readings?` and confirm structured readings display.
7. Ask an unsupported question and confirm the insufficient-evidence styling.
8. Submit an empty question and confirm the browser-side validation message.
9. Stop the backend, reload, and confirm the connection error is technician-friendly.
10. Restart the backend and verify `/docs`, `/api/health`, machine, sensor, and maintenance endpoints remain available.

## Testing

The repository has no frontend test runner. The UI is covered by direct browser
verification, while the backend suite remains the regression gate:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests -q
```

## Limitations

The chat is stateless because the backend chat endpoint is request-based. The
frontend does not persist conversation history. A live provider key and an
available local Qdrant index are still required for document-grounded answers;
unit tests continue to mock those integrations.
