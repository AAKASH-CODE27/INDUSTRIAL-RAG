# Industrial Maintenance RAG

AI-Powered Industrial Maintenance Support System using Retrieval-Augmented Generation (RAG).

## Live Demo

**Application:**  
https://industrial-rag.onrender.com/app/

**API Documentation:**  
https://industrial-rag.onrender.com/docs

---

## Overview

Industrial Maintenance RAG is an AI-powered maintenance support system designed to help users troubleshoot industrial machines using machine data and maintenance knowledge.

The system combines:

- Machine sensor data
- Failure records
- Maintenance records
- Industrial maintenance documents
- Semantic vector search
- Google Gemini

Instead of generating an answer only from the language model's internal knowledge, the system retrieves relevant maintenance information and machine-specific context before generating an answer.

### In Simple Terms

User Question
      ↓
Retrieve Relevant Maintenance Knowledge
      ↓
Retrieve Machine Sensor Information
      ↓
Combine Relevant Context
      ↓
Gemini
      ↓
Grounded Maintenance Response
      ↓
Answer + Sources


---

## Problem Statement

Industrial maintenance teams need quick access to machine conditions, maintenance history, failure information, and technical documentation when troubleshooting equipment.

Traditional document search requires engineers to manually search through multiple documents and records.

This project provides a conversational interface that retrieves relevant information and generates a maintenance-oriented response using machine-specific and document-based context.

---

## Objectives

- Provide machine-specific maintenance assistance.
- Retrieve relevant information from industrial documents.
- Combine document knowledge with machine data.
- Generate responses using retrieved evidence.
- Provide source information with generated responses.
- Provide REST APIs for accessing the system.
- Provide a simple web interface for maintenance queries.

---

## System Architecture


                         ┌──────────────────────┐
                         │        User          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Web Interface     │
                         │   HTML/CSS/JavaScript│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    FastAPI Backend   │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
             ┌────────────┐  ┌────────────┐  ┌────────────┐
             │ PostgreSQL │  │   Qdrant   │  │   Gemini   │
             │            │  │            │  │            │
             │ Machines   │  │ Document   │  │ Response   │
             │ Sensors    │  │ Embeddings │  │ Generation │
             │ Failures   │  │ Retrieval  │  │            │
             │ Maintenance│  │            │  │            │
             └─────┬──────┘  └──────┬─────┘  └──────┬─────┘
                   │                │               │
                   └────────────────┼───────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Grounded Maintenance │
                         │       Response       │
                         └──────────────────────┘


---

## RAG Pipeline

### 1. Document Ingestion

Industrial maintenance documents are processed before they are used for retrieval.

PDF Documents
      ↓
Text Extraction
      ↓
Text Cleaning
      ↓
Logical Chunking
      ↓
Embedding Generation
      ↓
Qdrant Vector Database


Each document chunk is converted into a vector embedding and stored in Qdrant together with relevant metadata.

### 2. Question Answering

When a user asks a question:

User Question
      ↓
Query Embedding
      ↓
Qdrant Semantic Search
      ↓
Relevant Document Chunks
      ↓
Machine Sensor Context
      ↓
Maintenance Context
      ↓
Context Assembly
      ↓
Gemini
      ↓
Structured Maintenance Answer
      ↓
Sources + Retrieval Information
```

The retrieved information provides project-specific context for the generated response.

---

## Data Sources

The system uses multiple types of information.

### Machine Data

The production system contains five machines:

- `CNC-001`
- `CNC-002`
- `LATHE-001`
- `PRESS-001`
- `MILL-001`

### Sensor Data

Machine telemetry includes:

- Temperature
- Vibration
- Pressure
- RPM
- Motor current

### Maintenance Data

The relational database contains:

- Machine information
- Failure records
- Maintenance records
- Sensor readings

### Document Knowledge

Industrial maintenance documents provide technical information used by the semantic retrieval system.

---

## Key Features

- Machine-specific maintenance assistance
- Semantic document retrieval
- Qdrant vector search
- Gemini-powered response generation
- PostgreSQL machine and maintenance data
- Sensor context integration
- Maintenance context integration
- Source-aware responses
- Retrieval confidence information
- Structured AI responses
- REST API
- Swagger API documentation
- Web-based frontend
- Production deployment

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Relational Database | PostgreSQL |
| Vector Database | Qdrant Cloud |
| LLM | Google Gemini |
| Embeddings | Gemini Embeddings |
| Document Processing | PyPDF |
| ORM | SQLAlchemy |
| API Server | Uvicorn |
| Deployment | Render |

---

## API Endpoints

### Health

GET /api/health

Checks the backend service status.

### Machines

GET /api/machines


Returns the registered machines.

### Sensors

GET /api/sensors

Returns sensor information.

### RAG Search 
POST /api/rag/search


Performs semantic retrieval against the maintenance knowledge base.

### Chat

POST /api/chat

Generates a machine-specific maintenance response using retrieved knowledge and machine context.

---

## API Documentation

Interactive Swagger documentation:

https://industrial-rag.onrender.com/docs

---

## Project Structure

INDUSTRIAL-RAG/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── scripts/
│   ├── tests/
│   ├── documents/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── docs/
│
├── README.md
└── .gitignore


---

## Local Development

### Prerequisites

Install:

- Python 3.11+
- PostgreSQL
- Qdrant
- Google Gemini API key

### 1. Clone the Repository

git clone https://github.com/AAKASH-CODE27/INDUSTRIAL-RAG.git
cd INDUSTRIAL-RAG


### 2. Create a Virtual Environment

python -m venv venv

#### Windows

venv\Scripts\activate


### 3. Install Backend Dependencies

cd backend
pip install -r requirements.txt


### 4. Configure Environment Variables

Create:

backend/.env

Add the required configuration:

env
GEMINI_API_KEY=your_gemini_api_key

GEMINI_MODEL=your_gemini_model
GEMINI_EMBEDDING_MODEL=your_embedding_model

QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=industrial_maintenance

DATABASE_URL=your_postgresql_connection_string

Never commit `.env` to GitHub.

Do not place API keys, database passwords, or Qdrant credentials in source code.

Use `.env.example` as the configuration template.

---

## Running the Backend

From the `backend` directory:

venv\Scripts\python -m uvicorn app.main:app --reload


Backend:

http://127.0.0.1:8000


Swagger:

http://127.0.0.1:8000/docs


---

## Running the Frontend

Open another terminal:

cd frontend
python -m http.server 5173


Open:

http://localhost:5173


## Testing

Run the backend test suite from the `backend` directory:

pytest -q


The project includes tests covering areas such as:

- API health
- Document processing
- Embeddings
- Retrieval
- Vector storage
- Chat functionality
- RAG behavior

---

## Production Deployment

The production application is deployed using Render.

### Application

https://industrial-rag.onrender.com/app/

### Backend

https://industrial-rag.onrender.com/

### Swagger

https://industrial-rag.onrender.com/docs

### Production Architecture


User Browser
     │
     ▼
Render
     │
     ▼
FastAPI Backend
     │
     ├──────────────► PostgreSQL
     │
     ├──────────────► Qdrant Cloud
     │
     └──────────────► Google Gemini

## Example Use Case

A user selects a machine and asks:


Why is the vibration level high and what maintenance action should be taken?


The system:

1. Identifies the selected machine.
2. Retrieves relevant sensor information.
3. Searches the maintenance knowledge base.
4. Retrieves relevant maintenance information.
5. Combines the retrieved information.
6. Sends the relevant context to Gemini.
7. Generates a structured maintenance response.
8. Returns supporting sources and retrieval information.

---

## Why RAG?

A general-purpose language model does not automatically know the project's specific machine data or maintenance documents.

RAG addresses this by retrieving relevant project information before generating the response.


Without RAG

Question
   ↓
LLM
   ↓
General Knowledge
   ↓
Answer


With RAG

Question
   ↓
Retrieve Relevant Evidence
   ↓
Machine + Maintenance Context
   ↓
LLM
   ↓
Grounded Answer


---

## Limitations

- The quality of the response depends on the quality and coverage of the available maintenance documents.
- Sensor data must be correctly associated with the corresponding machine.
- Generated responses should support maintenance decision-making rather than replace qualified maintenance procedures.
- Production industrial use would require approved manufacturer documentation, authentication, monitoring, and additional safety controls.

---

## Future Improvements

Possible future improvements include:

- Integration with real industrial IoT sensor streams
- Additional machine-specific maintenance manuals
- Automated anomaly detection
- Predictive maintenance models
- Role-based access control
- Maintenance work-order integration
- Historical sensor trend visualization
- Alert and notification systems
- Expanded evaluation datasets
- Improved observability and monitoring

---

## Author

**Aakash**

Industrial Maintenance RAG  
AI-Powered Industrial Maintenance Support System

GitHub:

https://github.com/AAKASH-CODE27/INDUSTRIAL-RAG
