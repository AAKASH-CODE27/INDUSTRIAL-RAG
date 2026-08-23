import json
from pathlib import Path

from app.rag.retriever import Retriever


EVALUATION_FILE = Path("data/rag_evaluation.json")


def load_evaluation_data():
    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def evaluate_query(
    retriever,
    item,
    top_k=5,
):
    query = item["query"]
    expected_documents = set(
        item["expected_documents"]
    )

    results = retriever.search(
        query=query,
        top_k=top_k,
    )

    retrieved_documents = [
        result["document_id"]
        for result in results
    ]

    hit = any(
        document in expected_documents
        for document in retrieved_documents
    )

    return {
        "query": query,
        "expected": list(expected_documents),
        "retrieved": retrieved_documents,
        "hit": hit,
    }


def main():

    print("=" * 70)
    print("PHASE 5.8 - RETRIEVAL EVALUATION")
    print("=" * 70)

    evaluation_data = load_evaluation_data()

    print(
        f"\nEvaluation queries: "
        f"{len(evaluation_data)}"
    )

    retriever = Retriever()

    results = []

    for index, item in enumerate(
        evaluation_data,
        start=1,
    ):

        result = evaluate_query(
            retriever,
            item,
            top_k=5,
        )

        results.append(result)

        status = "PASS" if result["hit"] else "FAIL"

        print("\n" + "-" * 70)
        print(f"Test #{index}")
        print(f"Query: {result['query']}")
        print(f"Expected: {result['expected']}")
        print(f"Retrieved: {result['retrieved']}")
        print(f"Result: {status}")

    total = len(results)

    passed = sum(
        result["hit"]
        for result in results
    )

    accuracy = (
        passed / total
        if total > 0
        else 0
    )

    print("\n" + "=" * 70)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Total queries : {total}")
    print(f"Passed        : {passed}")
    print(f"Failed        : {total - passed}")
    print(f"Accuracy@5    : {accuracy * 100:.2f}%")

    if accuracy >= 0.90:
        print("\nExcellent retrieval performance. ✅")

    elif accuracy >= 0.75:
        print("\nGood retrieval performance. ⚠️")

    else:
        print("\nRetrieval needs improvement. ❌")

    print("=" * 70)


if __name__ == "__main__":
    main()