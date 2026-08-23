from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingModel:
    def __init__(self):
        print(f"Loading embedding model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)

    def embed_text(self, text: str) -> list[float]:
        """
        Convert one text string into an embedding vector.
        """

        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")

        vector = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vector.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Convert multiple texts into embedding vectors.
        """

        if not texts:
            return []

        if any(not text or not text.strip() for text in texts):
            raise ValueError("Cannot embed empty text.")

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vectors.tolist()

    @property
    def dimension(self) -> int:
        return self.model.get_embedding_dimension()