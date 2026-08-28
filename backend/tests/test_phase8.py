from app.services.evidence_context import normalize_retrieved_chunks, source_references


def test_evidence_context_preserves_metadata_and_deduplicates_sources():
    chunks = normalize_retrieved_chunks(
        [
            {
                "text": "Inspect bearing alignment.",
                "score": 0.91,
                "chunk_id": "case-14-1",
                "document_id": "case-14",
                "document_name": "Troubleshooting Case 14",
                "source": "cases.csv",
            },
            {
                "text": "Check bearing wear.",
                "score": 0.82,
                "chunk_id": "case-14-2",
                "document_id": "case-14",
                "document_name": "Troubleshooting Case 14",
                "source": "cases.csv",
            },
        ]
    )

    sources = source_references(chunks)

    assert chunks[0].content == "Inspect bearing alignment."
    assert chunks[0].document_name == "Troubleshooting Case 14"
    assert sources == [
        {
            "chunk_id": "case-14-1",
            "document_id": "case-14",
            "document_name": "Troubleshooting Case 14",
            "score": 0.91,
            "source": "cases.csv",
        }
    ]


def test_rag_api_returns_mocked_top_k_results(client, monkeypatch):
    result = {"text": "Inspect the bearing.", "score": 0.9, "source": "cases.csv"}
    calls = []
    monkeypatch.setattr(
        "app.api.rag.retriever.search",
        lambda query, top_k: calls.append((query, top_k)) or [result],
    )

    response = client.post(
        "/api/rag/search",
        json={"query": "high vibration", "top_k": 3},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "high vibration",
        "results": [result],
    }
    assert calls == [("high vibration", 3)]


def test_rag_api_handles_no_results(client, monkeypatch):
    monkeypatch.setattr("app.api.rag.retriever.search", lambda query, top_k: [])

    response = client.post(
        "/api/rag/search",
        json={"query": "unsupported lubricant", "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["results"] == []