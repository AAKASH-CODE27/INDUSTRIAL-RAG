from pathlib import Path
from app.rag.loaders import load_documents
from app.rag.preprocessor import preprocess_document
from app.rag.chunker import chunk_documents
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore
from app.core.config import QDRANT_COLLECTION

DOCUMENT_DIR = Path("data/documents")

def main():
    print("=" * 70)
    print("DOCUMENT INGESTION PIPELINE")
    print("=" * 70)

    print("1. Loading raw documents...")
    raw_documents = load_documents(str(DOCUMENT_DIR))
    print(f"Loaded {len(raw_documents)} pages.")

    print("2. Preprocessing documents...")
    processed_documents = [preprocess_document(doc) for doc in raw_documents]

    print("3. Chunking documents...")
    chunks = chunk_documents(processed_documents)
    print(f"Created {len(chunks)} chunks.")

    print("4. Generating embeddings (this may take a minute)...")
    embedding_model = EmbeddingModel()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.embed_texts(texts)
    print(f"Generated {len(embeddings)} embeddings of dimension {embedding_model.dimension}.")

    print("5. Recreating Qdrant collection...")
    vector_store = VectorStore()
    vector_store.create_collection(
        vector_size=embedding_model.dimension,
        recreate=True,
    )

    print("6. Upserting vectors into Qdrant...")
    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )
    
    count = vector_store.count()
    print(f"\nIngestion complete! Successfully stored {count} vectors in collection '{QDRANT_COLLECTION}'.")

if __name__ == "__main__":
    main()
