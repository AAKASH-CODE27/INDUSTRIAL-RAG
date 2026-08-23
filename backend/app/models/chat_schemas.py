from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    machine_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value


class RetrievedChunk(BaseModel):
    chunk_id: int | str | None = None
    content: str
    score: float
    document_id: int | str | None = None
    document_name: str | None = None
    document_type: str | None = None
    machine_type: str | None = None
    section: str | None = None
    section_number: str | int | None = None
    page: int | str | None = None
    source: str | None = None


class ChatResponse(BaseModel):
    machine_id: int
    question: str
    answer: "MaintenanceAnswer"
    machine_context: dict[str, Any]
    sensor_context: dict[str, Any] | None = None
    sources: list[dict[str, Any]]
    retrieval_confidence: float
    grounded: bool


class MaintenanceAnswer(BaseModel):
    assessment: str
    possible_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    safety_considerations: list[str] = Field(default_factory=list)
    insufficient_information: bool = False

    model_config = ConfigDict(from_attributes=True)
