from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChatRequest(BaseModel):
    machine_id: int = Field(gt=0)
    question: str | None = Field(default=None, min_length=1, max_length=4000)
    message: str | None = Field(default=None, min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def normalize_question(self):
        # Prioritize message if provided and non-empty, otherwise fallback to question
        msg_val = self.message.strip() if self.message else ""
        q_val = self.question.strip() if self.question else ""

        # If question is the Swagger default "string" and message is given, prefer message
        if msg_val and (not q_val or q_val.lower() == "string"):
            chosen = msg_val
        elif q_val and q_val.lower() != "string":
            chosen = q_val
        elif msg_val:
            chosen = msg_val
        elif q_val:
            chosen = q_val
        else:
            raise ValueError("Question cannot be empty")

        self.question = chosen
        self.message = chosen
        return self



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
    maintenance_context: list[dict[str, Any]] = Field(default_factory=list)
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
