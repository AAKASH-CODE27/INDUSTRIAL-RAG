from collections.abc import Mapping, Sequence
from typing import Any

from app.models.chat_schemas import RetrievedChunk


SOURCE_FIELDS = {"chunk_id", "document_id", "document_name", "source", "score", "section", "page"}


def normalize_retrieved_chunks(raw_chunks: Sequence[Mapping[str, Any]] | None) -> list[RetrievedChunk]:
    if not raw_chunks:
        return []

    normalized: list[RetrievedChunk] = []
    saw_malformed = False
    for chunk in raw_chunks:
        if not isinstance(chunk, Mapping):
            saw_malformed = True
            continue
        content = chunk.get("text", chunk.get("content", ""))
        if content is None or content == "":
            saw_malformed = True
            continue
        payload = {key: value for key, value in chunk.items() if key not in {"text", "content"}}
        score = payload.get("score", 0.0)
        try:
            payload["score"] = float(score)
        except (TypeError, ValueError):
            payload["score"] = 0.0
        normalized.append(RetrievedChunk(content=str(content), **payload))

    if saw_malformed:
        return []
    return normalized


def source_references(chunks: Sequence[RetrievedChunk]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen_sources: set[Any] = set()
    for chunk in chunks:
        data = chunk.model_dump()
        source_key = data.get("document_id") or data.get("document_name") or data.get("source")
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        sources.append({key: value for key, value in data.items() if key in SOURCE_FIELDS and value is not None})
    return sources
