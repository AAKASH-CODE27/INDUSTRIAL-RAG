from pathlib import Path

from app.rag.loaders import load_documents
from app.rag.preprocessor import preprocess_document
from app.rag.chunker import chunk_documents
from app.rag.embeddings import EmbeddingModel


DOCUMENT_DIR = Path("data/documents")


def main():

    print("=" * 70)
    print("PHASE 5.5 - EMBEDDING TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1: Load
    # ---------------------------------------------------------

    raw_documents = load_documents(str(DOCUMENT_DIR))

    print(f"\nRaw pages loaded: {len(raw_documents)}")

    # ---------------------------------------------------------
    # STEP 2: Preprocess
    # ---------------------------------------------------------

    processed_documents = [
        preprocess_document(doc)
        for doc in raw_documents
    ]

    print(f"Processed documents: {len(processed_documents)}")

    # ---------------------------------------------------------
    # STEP 3: Chunk
    # ---------------------------------------------------------

    chunks = chunk_documents(processed_documents)

    print(f"Total chunks: {len(chunks)}")

    # ---------------------------------------------------------
    # STEP 4: Load embedding model
    # ---------------------------------------------------------

    embedding_model = EmbeddingModel()

    print(
        f"Embedding dimension: "
        f"{embedding_model.dimension}"
    )

    # ---------------------------------------------------------
    # STEP 5: Generate embeddings
    # ---------------------------------------------------------

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embedding_model.embed_texts(texts)

    print(
        f"Embeddings generated: "
        f"{len(embeddings)}"
    )

    # ---------------------------------------------------------
    # STEP 6: Validate
    # ---------------------------------------------------------

    assert len(embeddings) == len(chunks)

    for vector in embeddings:

        assert vector
        assert len(vector) == embedding_model.dimension

        # Because normalize_embeddings=True,
        # vector magnitude should be approximately 1.
        magnitude = sum(x * x for x in vector) ** 0.5

        assert 0.99 <= magnitude <= 1.01

    # ---------------------------------------------------------
    # STEP 7: Display sample
    # ---------------------------------------------------------

    print("\nSample embedding:")
    print("-" * 70)

    print(f"Chunk ID: {chunks[0]['chunk_id']}")
    print(f"Section : {chunks[0]['section']}")
    print(f"Text    : {chunks[0]['text'][:200]}")

    print("\nVector:")
    print(embeddings[0][:10])

    print(
        f"\nVector dimensions: "
        f"{len(embeddings[0])}"
    )

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ALL PHASE 5.5 CHECKS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()