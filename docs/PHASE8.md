# Phase 8: RAG-Powered Maintenance Chat

## Implemented pipeline

```text
Technician query
  -> ChatRequest validation
  -> existing Retriever.search()
  -> RetrievedChunk evidence normalization
  -> bounded machine, sensor, and maintenance context
  -> existing prompt builder
  -> existing OpenAI-compatible LLM adapter
  -> structured answer and backend-verified sources
```

The project reuses the Phase 5 embedding and local Qdrant vector store through
`app/rag/retriever.py`. No second index or provider abstraction was introduced.
The retriever returns scored chunks with the metadata available in the Qdrant
payload. `app/services/evidence_context.py` converts those records into the
validated evidence model and deduplicated source references.

## API

`POST /api/chat` accepts `machine_id`, `question` (or the backward-compatible
`message` field), and optional `top_k`. `top_k` is bounded from 1 through 20.
The response includes the structured answer, machine context, bounded sensor
and maintenance context, source metadata, retrieval confidence, and grounded
status.

`POST /api/rag/search` provides direct bounded retrieval with the same existing
retriever. Invalid queries or request values are rejected using FastAPI/Pydantic
validation, and no-result retrieval returns an empty result list.

## Grounding and safety

Document and hybrid chat questions require sufficiently relevant retrieved
chunks. Structured sensor-observation questions use verified database readings
and do not require document retrieval or an LLM call merely to report those
observations. Hybrid questions still require both sensor evidence and document
evidence. When evidence is absent or weak, the chat service returns a
structured insufficient-information answer.

The prompt is bounded by `CHAT_CONTEXT_MAX_CHARS`, recent sensor data is
bounded by `CHAT_SENSOR_READING_LIMIT`, maintenance history is bounded by
`CHAT_MAINTENANCE_RECORD_LIMIT`, and retrieval is bounded by `top_k <= 20`.
The LLM adapter uses environment configuration, bounded timeout/retry settings,
and is mocked in tests.

## Retrieval concepts

The embedding model converts maintenance text into vectors. Qdrant compares the
query vector with indexed vectors using the configured similarity metric and
returns the top-K scored chunks. Chunk metadata preserves document, section,
page, and source identity for attribution. Retrieval augments structured
machine data; it does not replace database facts.

## Manual verification

1. From `backend`, run `uvicorn app.main:app --reload`.
2. Open the FastAPI Swagger UI at `/docs`.
3. Try `POST /api/chat` with `{"machine_id": 1, "question": "Why is the vibration high?"}`.
4. Confirm the answer contains structured fields and verified `sources`.
5. Try an unsupported question and confirm `insufficient_information` is true.
6. Try a whitespace question or `top_k: 21` and confirm HTTP 422.
7. Try `POST /api/rag/search` with a maintenance query and inspect scored results.
8. Confirm health, machine, sensor, maintenance, and failure endpoints still respond.

## Limitations

The local Qdrant index must be built and available for document retrieval. The
LLM answer quality depends on provider availability and model behavior, although
provider failures are converted to bounded API errors. Source attribution is
limited to metadata present in indexed payloads. This system supports evidence-
based assistance and does not replace qualified maintenance procedures or
physical inspection.
