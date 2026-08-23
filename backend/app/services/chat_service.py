from time import perf_counter

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import CHAT_MIN_RETRIEVAL_SCORE
from app.core.logging_config import get_logger
from app.models.chat_schemas import ChatRequest, ChatResponse, MaintenanceAnswer, RetrievedChunk
from app.models.machine import Machine
from app.services import llm_service, retrieval_service
from app.services.prompt_service import build_maintenance_prompt
from app.services.sensor_service import get_latest_sensor_reading


logger = get_logger(__name__)


def _machine_context(machine: Machine) -> dict[str, object]:
    return {
        "id": machine.id,
        "machine_code": machine.machine_code,
        "name": machine.name,
        "machine_type": machine.machine_type,
        "location": machine.location,
        "status": machine.status,
    }


def _sensor_context(reading) -> dict[str, object] | None:
    if reading is None:
        return None
    return {
        "timestamp": reading.timestamp,
        "temperature": reading.temperature,
        "vibration": reading.vibration,
        "pressure": reading.pressure,
        "rpm": reading.rpm,
        "motor_current": reading.motor_current,
    }


def _source_references(chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
    sources = []
    seen_sources = set()
    for chunk in chunks:
        data = chunk.model_dump()
        source_key = data.get("document_id") or data.get("document_name") or data.get("source")
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        sources.append(
            {
                key: value
                for key, value in data.items()
                if key in {"chunk_id", "document_id", "document_name", "source", "score", "section", "page"}
                and value is not None
            }
        )
    return sources


def _abstention() -> MaintenanceAnswer:
    return MaintenanceAnswer(
        assessment="The available maintenance documentation does not provide enough information to determine the cause.",
        recommended_actions=["Review additional diagnostic data or relevant maintenance documentation."],
        safety_considerations=["Follow approved maintenance procedures and safety protocols."],
        insufficient_information=True,
    )


def handle_chat(request: ChatRequest, db: Session) -> ChatResponse:
    started_at = perf_counter()
    logger.info("Chat request received: machine_id=%s question_length=%s", request.machine_id, len(request.message))
    try:
        machine = db.query(Machine).filter(Machine.id == request.machine_id).first()
    except SQLAlchemyError as exc:
        logger.exception("Machine lookup failed: machine_id=%s", request.machine_id)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    retrieval_started_at = perf_counter()
    try:
        raw_chunks = retrieval_service.retriever.search(query=request.message, top_k=5)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Retrieval failed: machine_id=%s", request.machine_id)
        raise HTTPException(status_code=503, detail="Retrieval temporarily unavailable") from exc
    retrieval_ms = (perf_counter() - retrieval_started_at) * 1000

    try:
        sensor_context = _sensor_context(get_latest_sensor_reading(db, machine.id))
    except SQLAlchemyError as exc:
        logger.exception("Sensor lookup failed: machine_id=%s", request.machine_id)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    chunks = [
        RetrievedChunk(
            content=chunk.get("text", ""),
            **{key: value for key, value in chunk.items() if key != "text"},
        )
        for chunk in raw_chunks
    ]
    retrieval_confidence = max((chunk.score for chunk in chunks), default=0.0)
    grounded = retrieval_confidence >= CHAT_MIN_RETRIEVAL_SCORE
    sources = _source_references(chunks)

    if not chunks or not grounded:
        answer = _abstention()
        logger.info(
            "Chat abstained: machine_id=%s retrieval_count=%s retrieval_ms=%.1f total_ms=%.1f",
            request.machine_id,
            len(chunks),
            retrieval_ms,
            (perf_counter() - started_at) * 1000,
        )
        return ChatResponse(
            machine_id=machine.id,
            question=request.message,
            answer=answer,
            machine_context=_machine_context(machine),
            sensor_context=sensor_context,
            sources=sources,
            retrieval_confidence=retrieval_confidence,
            grounded=False,
        )

    prompt = build_maintenance_prompt(
        question=request.message,
        machine_context=_machine_context(machine),
        sensor_context=sensor_context,
        retrieved_chunks=[chunk.model_dump() for chunk in chunks],
    )
    llm_started_at = perf_counter()
    try:
        answer = llm_service.generate(prompt)
    except llm_service.LLMServiceError as exc:
        logger.error("LLM generation failed: machine_id=%s error_type=%s", request.machine_id, type(exc).__name__)
        raise HTTPException(status_code=503, detail="The maintenance assistant is temporarily unavailable") from exc
    llm_ms = (perf_counter() - llm_started_at) * 1000
    logger.info(
        "Chat succeeded: machine_id=%s retrieval_count=%s retrieval_ms=%.1f llm_ms=%.1f total_ms=%.1f model_configured=%s",
        request.machine_id,
        len(chunks),
        retrieval_ms,
        llm_ms,
        (perf_counter() - started_at) * 1000,
        bool(llm_service.LLM_MODEL),
    )
    return ChatResponse(
        machine_id=machine.id,
        question=request.message,
        answer=answer,
        machine_context=_machine_context(machine),
        sensor_context=sensor_context,
        sources=sources,
        retrieval_confidence=retrieval_confidence,
        grounded=grounded,
    )
