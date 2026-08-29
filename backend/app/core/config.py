import os

from dotenv import load_dotenv


load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_csv(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


APP_ENV = os.getenv("APP_ENV", "development")
APP_NAME = os.getenv("APP_NAME", "industrial-maintenance-ai")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./industrial_maintenance.db")
DB_ECHO = _get_bool("DB_ECHO", False)

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "600"))
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "1"))
LLM_RETRY_DELAY_SECONDS = float(os.getenv("LLM_RETRY_DELAY_SECONDS", "1"))

CHAT_CONTEXT_MAX_CHARS = int(os.getenv("CHAT_CONTEXT_MAX_CHARS", "12000"))
CHAT_MIN_RETRIEVAL_SCORE = float(os.getenv("CHAT_MIN_RETRIEVAL_SCORE", "0.45"))
CHAT_SENSOR_READING_LIMIT = int(os.getenv("CHAT_SENSOR_READING_LIMIT", "5"))
CHAT_MAINTENANCE_RECORD_LIMIT = int(os.getenv("CHAT_MAINTENANCE_RECORD_LIMIT", "3"))

CORS_ALLOWED_ORIGINS = _get_csv(
    "CORS_ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000",
)
FRONTEND_API_BASE_URL = os.getenv("FRONTEND_API_BASE_URL", "").rstrip("/")
QDRANT_PATH = os.getenv("QDRANT_PATH", "data/qdrant")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "industrial_maintenance")