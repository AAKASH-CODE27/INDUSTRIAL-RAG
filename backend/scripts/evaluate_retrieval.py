import json
from pathlib import Path

from app.rag.retriever import Retriever


EVALUATION_FILE = Path("data/rag_evaluation.json")


def load_evaluation_data():
    with open(EVALUATION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_document(result):
    return result.get("document_id") or result.get("document_name") or result.get("source") or "unknown"


def evaluate_query(retriever, item, top_k=5):
    query = item["query"]
    expected_documents = set(item.get("expected_documents", []))
    expected_abstain = bool(item.get("expected_abstain", False))

    results = retriever.search(query=query, top_k=top_k)
    retrieved_documents = [_normalize_document(result) for result in results]
    retrieved_scores = [float(result.get("score", 0.0)) for result in results]

    hit = any(document in expected_documents for document in retrieved_documents)
    max_score = max(retrieved_scores, default=0.0)
    abstain_actual = (not results) or (max_score < 0.45)
    abstention_match = abstain_actual == expected_abstain

    return {
        "query": query,
        "category": item.get("category", "unknown"),
        "expected": list(expected_documents),
        "retrieved": retrieved_documents,
        "hit": hit,
        "abstention_expected": expected_abstain,
        "abstention_actual": abstain_actual,
        "abstention_match": abstention_match,
    }


def main():
    print("=" * 70)
    print("PHASE 10 - RETRIEVAL EVALUATION")
    print("=" * 70)

    evaluation_data = load_evaluation_data()
    retriever = Retriever()
    results = []

    for index, item in enumerate(evaluation_data, start=1):
        result = evaluate_query(retriever, item, top_k=5)
        results.append(result)

        status = "PASS" if result["hit"] else "FAIL"
        print("\n" + "-" * 70)
        print(f"Test #{index} | {result['category']}")
        print(f"Query: {result['query']}")
        print(f"Expected: {result['expected']}")
        print(f"Retrieved: {result['retrieved']}")
        print(f"Retrieval: {status}")
        print(f"Abstention expected={result['abstention_expected']} actual={result['abstention_actual']}")

    total = len(results)
    retrieval_hits = sum(result["hit"] for result in results)
    abstention_matches = sum(result["abstention_match"] for result in results)
    retrieval_hit_rate = retrieval_hits / total if total else 0
    abstention_accuracy = abstention_matches / total if total else 0

    print("\n" + "=" * 70)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total queries            : {total}")
    print(f"Retrieval hits           : {retrieval_hits}")
    print(f"Retrieval hit rate       : {retrieval_hit_rate * 100:.2f}%")
    print(f"Abstention accuracy      : {abstention_accuracy * 100:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()