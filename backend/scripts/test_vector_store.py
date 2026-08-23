from pathlib import Path

from app.rag.loaders import load_documents
from app.rag.preprocessor import preprocess_document
from app.rag.chunker import chunk_documents
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore


DOCUMENT_DIR = Path("data/documents")


def main():

    print("=" * 70)
    print("PHASE 5.6 - VECTOR DATABASE TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1: Load PDFs
    # ---------------------------------------------------------

    raw_documents = load_documents(
        str(DOCUMENT_DIR)
    )

    print(f"\nRaw pages loaded: {len(raw_documents)}")

    # ---------------------------------------------------------
    # STEP 2: Preprocess
    # ---------------------------------------------------------

    processed_documents = [
        preprocess_document(doc)
        for doc in raw_documents
    ]

    print(
        f"Processed documents: "
        f"{len(processed_documents)}"
    )

    # ---------------------------------------------------------
    # STEP 3: Chunk
    # ---------------------------------------------------------

    chunks = chunk_documents(
        processed_documents
    )

    print(f"Total chunks: {len(chunks)}")

    # ---------------------------------------------------------
    # STEP 4: Embeddings
    # ---------------------------------------------------------

    embedding_model = EmbeddingModel()

    print(
        f"Embedding dimension: "
        f"{embedding_model.dimension}"
    )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embedding_model.embed_texts(
        texts
    )

    print(
        f"Embeddings generated: "
        f"{len(embeddings)}"
    )

    # ---------------------------------------------------------
    # STEP 5: Vector database
    # ---------------------------------------------------------

    vector_store = VectorStore()

    vector_store.create_collection(
        vector_size=embedding_model.dimension,
        recreate=True,
    )

    print(
        f"Collection created: "
        f"industrial_maintenance"
    )

    # ---------------------------------------------------------
    # STEP 6: Store vectors
    # ---------------------------------------------------------

    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    print("Chunks inserted into Qdrant.")

    # ---------------------------------------------------------
    # STEP 7: Verify count
    # ---------------------------------------------------------

    stored_count = vector_store.count()

    print(
        f"Vectors stored: "
        f"{stored_count}"
    )

    assert stored_count == len(chunks)

    # ---------------------------------------------------------
    # STEP 8: Collection information
    # ---------------------------------------------------------

    info = vector_store.get_collection_info()

    print("\nCollection information:")
    print("-" * 70)

    print(
        f"Vector size: "
        f"{info.config.params.vectors.size}"
    )

    print(
        f"Distance: "
        f"{info.config.params.vectors.distance}"
    )

    print(
        f"Points count: "
        f"{stored_count}"
    )

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ALL PHASE 5.6 CHECKS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()