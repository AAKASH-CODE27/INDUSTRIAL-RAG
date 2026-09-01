# Industrial Maintenance RAG

An industrial maintenance assistant that combines machine context, sensor telemetry, historical maintenance data, and retrieval-augmented generation (RAG) to answer technician questions grounded in equipment documentation and local operational history.

## Problem

Industrial maintenance teams need fast, contextual answers to questions like:

- Why is vibration unusually high on a motor?
- What maintenance procedure applies to this equipment?
- Which safety steps are required before inspection?
- Are the current sensor readings consistent with prior failures or known issues?

The project delivers a production-minded backend and frontend that route these questions through validation, retrieval, and grounded answer generation while reducing unsupported claims.

## Solution overview

The system combines:

- a FastAPI backend with validation and safety checks
- SQLAlchemy models for machines, failures, maintenance, and sensor readings
- a document ingestion and retrieval pipeline using embeddings and Qdrant-like vector storage
- context assembly that mixes sensor context, maintenance history, and retrieved evidence
- a grounded maintenance assistant that abstains when evidence is missing or weak
- a lightweight frontend for technician interaction

## Architecture

User
↓
Frontend
↓
FastAPI API
↓
Validation + request routing
↓
RAG / Retrieval layer
↓
Context assembly (sensor + maintenance + docs)
↓
LLM answer generation
↓
Grounded response + source references

Sensors
↓
Database
↓
Anomaly / maintenance intelligence
↓
API and chat context

## Technology stack

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite in development/test mode
- Pydantic validation
- Python-dotenv configuration
- Qdrant-compatible vector retrieval
- SentenceTransformers / embeddings
- Pytest for regression testing
- Vanilla JavaScript frontend

## Repository layout

- backend/app — FastAPI app, routes, models, services, RAG modules
- backend/data — stored evaluation data, vector metadata, sample documents
- backend/scripts — setup, data generation, evaluation utilities
- backend/tests — unit and integration regression tests
- frontend — technician-facing interface
- docs — project documentation and phase notes

## Backend setup

1. Open a terminal in the repository root.
2. Change into the backend folder.
3. Create or activate the virtual environment.
4. Install dependencies:

   pip install -r requirements.txt

5. Copy the example environment file if needed:

   copy backend\.env.example backend\.env

6. Start the API:

   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

7. Verify the API:

   http://127.0.0.1:8000/docs

## Frontend setup

Open the app by serving the frontend from the same backend or via a static host. The frontend reads the backend base URL from the page or from a global variable when present.

Typical local flow:

- start the backend on port 8000
- open the frontend page via the repository static mount, or serve the frontend files in a local web server
- confirm the machine list loads and the chat flow is reachable

## Environment variables

The project uses environment variables through Python-dotenv. A safe example is in:

- backend/.env.example

Relevant variables include:

- DATABASE_URL
- LLM_API_KEY
- LLM_BASE_URL
- LLM_MODEL
- CHAT_MIN_RETRIEVAL_SCORE
- CORS_ALLOWED_ORIGINS
- QDRANT_PATH
- QDRANT_COLLECTION
- APP_ENV
- LOG_LEVEL

Never commit a real .env file with production credentials.

## RAG pipeline

The application flow is:

1. User sends a machine-specific question.
2. The request is validated and normalized.
3. Machine context and recent sensor data are loaded.
4. The retriever searches indexed maintenance documents.
5. Retrieved chunks are normalized, filtered, and scored.
6. A prompt is assembled using machine context, maintenance history, and evidence.
7. The LLM is called only when the evidence is sufficiently grounded.
8. If the evidence is weak or missing, the system abstains and clearly explains the limitation.
9. Sources are returned to the frontend for traceability.

## Sensor and anomaly flow

The system also supports checking machine health through sensor and maintenance records:

- sensor readings are queried by machine and time window
- maintenance history provides context for prior issues
- raw data is normalized into answer-friendly summaries
- anomaly and maintenance logic can be surfaced through the API and chat interface

## Testing

Run the full test suite with:

cd backend
python -m pytest tests -q

The project includes test coverage for:

- health and validation endpoints
- machine and sensor flows
- anomaly and maintenance logic
- chat and retrieval resilience
- LLM/provider error handling
- end-to-end chat validation

## Evaluation

The retrieval evaluation dataset is stored in:

- backend/data/rag_evaluation.json

The evaluation script is:

- backend/scripts/evaluate_retrieval.py

Run it with:

cd backend
python scripts/evaluate_retrieval.py

This script calculates retrieval hit rate and abstention alignment using the dataset currently checked into the repo. It does not fabricate metrics.

## Demo flow

A representative flow is:

1. start backend
2. confirm /api/health works
3. select a machine in the frontend
4. ask a maintenance question
5. review returned sources and answer
6. try a low-confidence or unsupported question to confirm abstention behavior
7. confirm invalid requests yield 422 responses and unavailable services yield 503-style behavior

## Known limitations

- The default environment is designed for local development and testing.
- Real vector indexes and LLM service configuration must be supplied in a production environment.
- Retrieval quality depends on the indexed documents, embeddings, and dataset quality.
- The system is grounded and cautious, which means it may abstain rather than speculate when evidence is insufficient.

## Future improvements

- richer document ingestion and metadata normalization
- stronger evaluation scoring for answer correctness and faithfulness
- runtime monitoring and structured observability dashboards
- production deployment hardening and secret management
- broader live-model integration and model fallback policies
