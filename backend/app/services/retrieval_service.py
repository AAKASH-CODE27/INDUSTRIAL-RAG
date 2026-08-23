from app.rag.retriever import Retriever


# Shared by the RAG endpoint and chat orchestration to preserve Phase 5 behavior.
retriever = Retriever()
