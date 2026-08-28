from collections.abc import Mapping, Sequence
from typing import Any

from app.models.chat_schemas import RetrievedChunk


SOURCE_FIELDS = {"chunk_id", "document_id", "document_name", "source", "score", "section", "page"}


def normalize_retrieved_chunks(raw_chunks: Sequence[Mapping[str, Any]]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            content=str(chunk.get("text", chunk.get("content", ""))),
            **{key: value for key, value in chunk.items() if key not in {"text", "content"}},
        )
        for chunk in raw_chunks
    ]


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
