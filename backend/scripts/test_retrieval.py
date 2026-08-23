from app.rag.retriever import Retriever


def main():

    print("=" * 70)
    print("PHASE 5.7 - RETRIEVAL TEST")
    print("=" * 70)

    retriever = Retriever()

    queries = [
        "Why is spindle vibration increasing?",
        "What causes high motor current?",
        "What are signs of bearing degradation?",
        "What causes low hydraulic pressure?",
        "What should be checked before machine maintenance?",
        "What does error E104 indicate?",
        "What causes unstable RPM?",
        "What should be checked when vibration and temperature increase?",
    ]

    for query in queries:

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = retriever.search(
            query=query,
            top_k=3,
        )

        assert results

        for index, result in enumerate(
            results,
            start=1,
        ):

            print("\n" + "-" * 70)

            print(f"Result #{index}")
            print(f"Score        : {result['score']:.4f}")
            print(f"Document     : {result['document_name']}")
            print(f"Type         : {result['document_type']}")
            print(f"Machine      : {result['machine_type']}")
            print(f"Section      : {result['section']}")
            print(f"Page         : {result['page']}")
            print(f"Source       : {result['source']}")
            print(f"Chunk ID     : {result['chunk_id']}")

            print("\nText:")
            print(result["text"][:500])

    print("\n" + "=" * 70)
    print("RETRIEVAL TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()