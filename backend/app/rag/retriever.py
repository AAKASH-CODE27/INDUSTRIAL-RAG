from .embeddings import EmbeddingModel
from .vector_store import VectorStore, COLLECTION_NAME


class Retriever:

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search the vector database for semantically
        similar industrial maintenance chunks.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        # Convert user query into embedding
        query_vector = self.embedding_model.embed_text(query)

        # Search Qdrant
        results = self.vector_store.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        ).points

        formatted_results = []

        for result in results:

            payload = result.payload or {}

            formatted_results.append(
                {
                    "score": float(result.score),
                    "text": payload.get("text", ""),
                    "chunk_id": payload.get("chunk_id"),
                    "document_id": payload.get("document_id"),
                    "document_name": payload.get("document_name"),
                    "document_type": payload.get("document_type"),
                    "machine_type": payload.get("machine_type"),
                    "section": payload.get("section"),
                    "section_number": payload.get("section_number"),
                    "page": payload.get("page"),
                    "source": payload.get("source"),
                }
            )

        return formatted_results