from app.core.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL
from app.services.gemini_provider import GeminiProvider, GeminiProviderError


MODEL_NAME = GEMINI_EMBEDDING_MODEL

_MODEL_DIMENSIONS = {
    "text-embedding-004": 768,
    "gemini-embedding-001": 3072,
    "gemini-embedding-2-preview": 3072,
    "gemini-embedding-2": 3072,
}


class EmbeddingModel:
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = (api_key or GEMINI_API_KEY or "").strip()
        self.model_name = (model_name or MODEL_NAME or "gemini-embedding-001").strip().removeprefix("models/")
        self.provider = GeminiProvider(api_key=self.api_key, embedding_model=self.model_name)
        self._dimension: int | None = _MODEL_DIMENSIONS.get(self.model_name.lower(), None)

    def embed_text(self, text: str) -> list[float]:
        """
        Convert one text string into an embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")
        try:
            vector = self.provider.embed_text(text)
            self._dimension = len(vector)
            return vector
        except GeminiProviderError as exc:
            raise ValueError(str(exc)) from exc

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Convert multiple texts into embedding vectors.
        """
        if not texts:
            return []
        if any(not text or not text.strip() for text in texts):
            raise ValueError("Cannot embed empty text.")
        vectors: list[list[float]] = []
        for text in texts:
            vectors.append(self.embed_text(text))
        return vectors

    @property
    def dimension(self) -> int:
        if self._dimension is not None:
            return self._dimension
        normalized = self.model_name.lower().removeprefix("models/")
        if normalized in _MODEL_DIMENSIONS:
            self._dimension = _MODEL_DIMENSIONS[normalized]
            return self._dimension
        raise ValueError(f"Unsupported Gemini embedding model: {self.model_name}")