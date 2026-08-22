from pathlib import Path

from app.rag.loaders import load_documents
from app.rag.preprocessor import preprocess_document


DOCUMENT_DIR = Path("data/documents")


def main():
    print("=" * 70)
    print("PHASE 5.3 - TEXT CLEANING + METADATA TEST")
    print("=" * 70)

    raw_documents = load_documents(str(DOCUMENT_DIR))

    print(f"\nRaw pages loaded: {len(raw_documents)}")

    processed_documents = [
        preprocess_document(doc)
        for doc in raw_documents
    ]

    print(f"Processed pages: {len(processed_documents)}")

    print("\nSample processed document:")

    doc = processed_documents[0]

    print("-" * 70)
    print(f"Document ID   : {doc['document_id']}")
    print(f"Document Name : {doc['document_name']}")
    print(f"Document Type : {doc['document_type']}")
    print(f"Machine Type  : {doc['machine_type']}")
    print(f"Page          : {doc['page']}")
    print(f"Section       : {doc['section']}")
    print(f"Source        : {doc['source']}")

    print("\nCleaned text:")
    print(doc["text"][:1000])

    print("\n" + "=" * 70)

    # Validation
    assert doc["text"]
    assert doc["page"] == 1
    assert doc["source"]
    assert doc["document_id"]
    assert doc["document_name"]
    assert doc["document_type"]
    assert doc["machine_type"]
    assert doc["section"]

    # Ensure synthetic notice was removed
    assert "Synthetic project reference document" not in doc["text"]

    print("ALL PHASE 5.3 CHECKS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()