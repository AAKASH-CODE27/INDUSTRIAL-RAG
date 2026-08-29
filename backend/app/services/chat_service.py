from time import perf_counter

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import (
    CHAT_MAINTENANCE_RECORD_LIMIT,
    CHAT_MIN_RETRIEVAL_SCORE,
    CHAT_SENSOR_READING_LIMIT,
)
from app.core.logging_config import get_logger
from app.models.chat_schemas import ChatRequest, ChatResponse, MaintenanceAnswer
from app.models.machine import Machine
from app.models.maintenance import MaintenanceRecord
from app.services import llm_service, retrieval_service
from app.services.evidence_context import normalize_retrieved_chunks, source_references
from app.services.prompt_service import build_maintenance_prompt
from app.services.sensor_service import get_recent_sensor_readings


logger = get_logger(__name__)
SENSOR_TERMS = {
    "sensor",
    "reading",
    "readings",
    "temperature",
    "vibration",
    "pressure",
    "rpm",
    "current",
}
DOCUMENT_TERMS = {
    "document",
    "documentation",
    "manual",
    "procedure",
    "maintenance",
    "cause",
    "causing",
    "inspect",
    "diagnose",
}
STRUCTURED_SENSOR_TERMS = {
    "latest",
    "recent",
    "reading",
    "readings",
    "value",
    "values",
    "show",
    "list",
}


def _machine_context(machine: Machine) -> dict[str, object]:
    return {
        "id": machine.id,
        "machine_code": machine.machine_code,
        "name": machine.name,
        "machine_type": machine.machine_type,
        "location": machine.location,
        "status": machine.status,
    }


def _sensor_values(reading) -> dict[str, object]:
    return {
        "timestamp": reading.timestamp,
        "temperature": reading.temperature,
        "vibration": reading.vibration,
        "pressure": reading.pressure,
        "rpm": reading.rpm,
        "motor_current": reading.motor_current,
    }


def _sensor_context(readings) -> dict[str, object] | None:
    if not readings:
        return None
    return {
        **_sensor_values(readings[0]),
        "recent_readings": [_sensor_values(reading) for reading in readings],
    }


def _maintenance_context(records) -> list[dict[str, object]]:
    return [
        {
            "id": record.id,
            "maintenance_type": record.maintenance_type,
            "description": record.description,
            "findings": record.findings,
            "action_taken": record.action_taken,
            "parts_replaced": record.parts_replaced,
            "performed_at": record.performed_at,
        }
        for record in records
    ]


def _question_route(question: str) -> str:
    words = set(question.lower().replace("?", " ").split())
    has_sensor_terms = bool(words & SENSOR_TERMS)
    has_document_terms = bool(words & DOCUMENT_TERMS)
    asks_for_sensor_observation = bool(words & STRUCTURED_SENSOR_TERMS)
    asks_for_explanation = bool(words & {"why", "cause", "causing", "explain", "problem", "issue"})
    if has_sensor_terms and has_document_terms:
        return "hybrid"
    if has_sensor_terms and asks_for_sensor_observation and not asks_for_explanation:
        return "sensor"
    return "document"


def _abstention() -> MaintenanceAnswer:
    return MaintenanceAnswer(
        assessment="The available machine data and maintenance evidence are not sufficient to answer this question reliably.",
        recommended_actions=["Review additional diagnostic data or relevant maintenance documentation."],
        safety_considerations=["Follow approved maintenance procedures and safety protocols."],
        insufficient_information=True,
    )


def _sensor_answer(sensor_context: dict[str, object]) -> MaintenanceAnswer:
    latest_values = [
        f"{label} = {sensor_context[field]}"
        for field, label in (
            ("temperature", "temperature"),
            ("vibration", "vibration"),
            ("pressure", "pressure"),
            ("rpm", "RPM"),
            ("motor_current", "motor current"),
        )
        if sensor_context.get(field) is not None
    ]
    return MaintenanceAnswer(
        assessment=(
            "The latest available sensor readings are: "
            + ", ".join(latest_values)
            + "."
        ),
        safety_considerations=[
            "Treat these readings as observations and follow approved maintenance procedures for interpretation."
        ],
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
        raw_chunks = retrieval_service.retriever.search(query=request.message, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Retrieval failed: machine_id=%s", request.machine_id)
        raise HTTPException(status_code=503, detail="Retrieval temporarily unavailable") from exc
    retrieval_ms = (perf_counter() - retrieval_started_at) * 1000

    try:
        sensor_context = _sensor_context(
            get_recent_sensor_readings(db, machine.id, limit=max(1, CHAT_SENSOR_READING_LIMIT))
        )
        maintenance_context = _maintenance_context(
            db.query(MaintenanceRecord)
            .filter(MaintenanceRecord.machine_id == machine.id)
            .order_by(MaintenanceRecord.performed_at.desc())
            .limit(max(0, CHAT_MAINTENANCE_RECORD_LIMIT))
            .all()
        )
    except SQLAlchemyError as exc:
        logger.exception("Sensor lookup failed: machine_id=%s", request.machine_id)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    try:
        chunks = normalize_retrieved_chunks(raw_chunks)
    except (AttributeError, TypeError, ValueError) as exc:
        logger.warning("Malformed retrieval payload ignored: machine_id=%s error=%s", request.machine_id, exc)
        chunks = []
    retrieval_confidence = max((chunk.score for chunk in chunks), default=0.0)
    question_route = _question_route(request.message)
    has_sensor_evidence = sensor_context is not None
    has_document_evidence = bool(chunks) and retrieval_confidence >= CHAT_MIN_RETRIEVAL_SCORE
    if question_route == "sensor":
        grounded = has_sensor_evidence
    elif question_route == "hybrid":
        grounded = has_sensor_evidence and has_document_evidence
    else:
        grounded = has_document_evidence
    sources = source_references(chunks)

    if not grounded:
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
            maintenance_context=maintenance_context,
            sources=sources,
            retrieval_confidence=retrieval_confidence,
            grounded=False,
        )

    if question_route == "sensor":
        answer = _sensor_answer(sensor_context)
        return ChatResponse(
            machine_id=machine.id,
            question=request.message,
            answer=answer,
            machine_context=_machine_context(machine),
            sensor_context=sensor_context,
            maintenance_context=maintenance_context,
            sources=sources,
            retrieval_confidence=retrieval_confidence,
            grounded=True,
        )

    prompt = build_maintenance_prompt(
        question=request.message,
        machine_context=_machine_context(machine),
        sensor_context=sensor_context,
        maintenance_context=maintenance_context,
        retrieved_chunks=[chunk.model_dump() for chunk in chunks],
    )
    llm_started_at = perf_counter()
    try:
        answer = llm_service.generate(prompt)
        if answer is None:
            raise llm_service.LLMServiceError("LLM provider returned no answer")
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
        maintenance_context=maintenance_context,
        sources=sources,
        retrieval_confidence=retrieval_confidence,
        grounded=grounded,
    )
