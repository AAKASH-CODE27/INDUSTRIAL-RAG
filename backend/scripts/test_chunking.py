from pathlib import Path

from app.rag.loaders import load_documents
from app.rag.preprocessor import preprocess_document
from app.rag.chunker import chunk_documents


DOCUMENT_DIR = Path("data/documents")


def main():

    print("=" * 70)
    print("PHASE 5.4 - INTELLIGENT CHUNKING TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1: Load PDFs
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

    print(
        f"Processed documents: "
        f"{len(processed_documents)}"
    )

    # ---------------------------------------------------------
    # STEP 3: Chunk
    # ---------------------------------------------------------

    chunks = chunk_documents(processed_documents)

    print(f"Total chunks created: {len(chunks)}")

    # ---------------------------------------------------------
    # STEP 4: Display chunks
    # ---------------------------------------------------------

    print("\nCHUNKS")
    print("=" * 70)

    for chunk in chunks:

        print("\n" + "-" * 70)

        print(f"Chunk ID       : {chunk['chunk_id']}")
        print(f"Document       : {chunk['document_name']}")
        print(f"Document Type  : {chunk['document_type']}")
        print(f"Machine Type   : {chunk['machine_type']}")
        print(f"Page           : {chunk['page']}")
        print(f"Section Number : {chunk['section_number']}")
        print(f"Section        : {chunk['section']}")
        print(f"Source         : {chunk['source']}")

        print("\nText:")
        print(chunk["text"][:400])

    # ---------------------------------------------------------
    # STEP 5: Validation
    # ---------------------------------------------------------

    assert len(chunks) > len(processed_documents)

    for chunk in chunks:

        assert chunk["chunk_id"]
        assert chunk["text"]

        assert chunk["document_id"]
        assert chunk["document_name"]

        assert chunk["document_type"]
        assert chunk["machine_type"]

        assert chunk["page"] >= 1

        assert chunk["section"]
        assert chunk["source"]

    # ---------------------------------------------------------
    # STEP 6: Check documents
    # ---------------------------------------------------------

    document_ids = set(
        chunk["document_id"]
        for chunk in chunks
    )

    assert len(document_ids) == 8

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ALL PHASE 5.4 CHECKS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()