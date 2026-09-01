from app.core.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL
from app.services.gemini_provider import GeminiProvider, GeminiProviderError


MODEL_NAME = GEMINI_EMBEDDING_MODEL


class EmbeddingModel:
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = (api_key or GEMINI_API_KEY or "").strip()
        self.model_name = model_name or MODEL_NAME
        self.provider = GeminiProvider(api_key=self.api_key, embedding_model=self.model_name)

    def embed_text(self, text: str) -> list[float]:
        """
        Convert one text string into an embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")
        try:
            return self.provider.embed_text(text)
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
        return 768