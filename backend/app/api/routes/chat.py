from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat_schemas import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat


router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Generate a grounded industrial maintenance answer",
    description="Combines machine data, the latest sensor reading, and maintenance documents into one structured answer.",
)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return handle_chat(request, db)
