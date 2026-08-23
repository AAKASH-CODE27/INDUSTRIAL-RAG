from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.retrieval_service import retriever


router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"],
)


class RAGSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Industrial maintenance question",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )


@router.post("/search")
def search_documents(request: RAGSearchRequest):

    try:
        results = retriever.search(
            query=request.query,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "results": results,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(exc)}",
        )