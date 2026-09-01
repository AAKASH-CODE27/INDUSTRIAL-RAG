# Architecture Overview

## Application layers

The repository is organized around a clean layered design for industrial maintenance tooling.

### 1. Frontend

The frontend is a lightweight JavaScript interface that presents:

- machine selection
- question entry
- answer output
- source references
- sensor and machine context
- error states

It communicates with the FastAPI backend through the REST API.

### 2. API layer

The backend app is initialized in [backend/app/main.py](../backend/app/main.py). It includes:

- CORS configuration
- request timing middleware
- validation error handling
- database error handling
- static frontend hosting
- route registration for health, machines, sensors, anomalies, failures, maintenance, RAG, and chat

### 3. Domain and data models

The application uses Pydantic schemas and SQLAlchemy models for:

- machine metadata
- sensor readings
- failures
- maintenance records
- chat and retrieval payloads

These are defined under the backend models and database modules.

### 4. Retrieval and RAG

The RAG stack covers:

- document ingestion and cleaning
- chunking
- embedding generation
- vector storage and search
- retrieved chunk normalization
- evidence filtering and scoring
- prompt construction for the LLM

The chat service orchestrates this flow using the retriever and evidence context helpers.

### 5. LLM orchestration

The LLM service is responsible for:

- configuration checks
- request generation
- retries for transient errors
- timeout and provider failure handling
- enforcing a no-answer guard

The chat service does not blindly trust provider output; it verifies groundedness before returning a final answer.

### 6. Safety and responsible-AI behavior

The project explicitly avoids unsupported claims by:

- checking retrieval confidence thresholds
- requiring sufficient evidence for non-sensor questions
- abstaining on weak or empty evidence
- surfacing source references
- distinguishing observations from interpreted guidance

This is especially important in maintenance tasks where incorrect instructions can create real risk.

## Runtime interaction

### Chat request flow

User query
↓
API validation
↓
Machine lookup
↓
Sensor and maintenance context load
↓
Retrieval search
↓
Evidence normalization + score filtering
↓
Groundedness decision
↓
LLM call when evidence is sufficient
↓
Response with answer + sources + confidence

### Sensor and maintenance data flow

Sensor readings
↓
Database persistence
↓
Recent reading retrieval
↓
Machine-specific summary
↓
Context used in decision support and RAG prompts

## Operational assumptions

- SQLite is used for local development and tests.
- A vector store compatible with the retriever implementation is required for actual retrieval.
- LLM access requires a configured provider endpoint and key in the current environment.
- The architecture favors grounded, cautious behavior over speculative answers.
