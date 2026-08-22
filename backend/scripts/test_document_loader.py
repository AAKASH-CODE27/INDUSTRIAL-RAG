from pathlib import Path

from app.rag.loaders import load_documents

DOCUMENT_DIR = Path("data/documents")

def main():
    print("=" * 60)
    print("PHASE 5.2 - DOCUMENT LOADER TEST")
    print("=" * 60)

    documents = load_documents(str(DOCUMENT_DIR))

    sources = sorted(set(doc["source"] for doc in documents))

    print(f"\nPDF files found : {len(sources)}")
    print(f"Pages extracted : {len(documents)}")

    print("\nDocuments:")
    for source in sources:
        page_count = sum(
            1 for doc in documents
            if doc["source"] == source
        )

        print(f"  ✓ {source} ({page_count} pages)")

    print("\nSample extracted content:")

    for doc in documents[:3]:
        print("\n" + "-" * 60)
        print(f"Source : {doc['source']}")
        print(f"Page   : {doc['page']}")
        print(f"ID     : {doc['document_id']}")
        print(f"Text   : {doc['text'][:500]}")

    print("\n" + "=" * 60)
    print("DOCUMENT LOADER TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()