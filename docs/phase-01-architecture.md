**# Phase 1 Backend Architecture**

## Overview

Phase 1 delivers a **topic → script pipeline** with:
- FastAPI backend for HTTP API
- SQLite for persistence
- Mock LLM layer (Ollama-ready)
- State machine for topic transitions
- Async job queue for background tasks

## Architecture

```
┌─────────────────────────────────────┐
│         Electron Frontend           │
│         (Phase 2: React UI)         │
└────────────────┬────────────────────┘
                 │ HTTP REST
                 ▼
┌──────────────────────────────────────┐
│         FastAPI Backend              │
│  ┌────────────────────────────────┐  │
│  │    API Layer                   │  │
│  │  - /api/topics                 │  │
│  │  - /api/scripts                │  │
│  │  - /api/pipeline               │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  LLM Layer (Mock)              │  │
│  │  - MockLLMProvider             │  │
│  │  - OllamaProvider (standby)    │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  Pipeline Orchestrator         │  │
│  │  - State Machine               │  │
│  │  - Job Queue                   │  │
│  └────────────────────────────────┘  │
└────────┬──────────────────────┬───────┘
         │                      │
         ▼                      ▼
    ┌────────────┐         ┌─────────────┐
    │  SQLite DB │         │ File System │
    │  (Queries) │         │   (Assets)  │
    └────────────┘         └─────────────┘
```

## State Machine

Topics flow through states:

```
DISCOVERED ──(approve)──> APPROVED ──(start_research)──> RESEARCHING ──(complete)──> RESEARCH_COMPLETE
                                ▲                                                          │
                                └──(reject) DELETED                                       │
                                                                                           ▼
                                                                         SCRIPT_DRAFTED ──(approve)──> SCRIPT_APPROVED
```

**Valid transitions** defined in `backend/pipeline/orchestrator.py:VALID_TRANSITIONS`

## Key Components

### 1. **Database Layer** (`backend/core/database.py`)
- SQLite connection management
- Schema initialization from `database/schema.sql`
- Query execution helpers

### 2. **Configuration** (`backend/core/config.py`)
- Pydantic Settings for environment variables
- LLM provider selection
- Ollama connection details

### 3. **Pydantic Models**
- `TopicResponse`, `TopicCreate` - Topic schema
- `ScriptResponse`, `ScriptCreate`, `ScriptUpdate` - Script schema
- `JobResponse` - Job/task schema

### 4. **LLM Provider Interface**
- `LLMProvider` (abstract base)
- `MockLLMProvider` - Synthetic data (current)
- `OllamaProvider` - Local model calls
- Factory pattern in `backend/llm/__init__.py`

### 5. **API Routes**
- `POST /api/topics/generate` - Create mock topics
- `POST /api/topics/{id}/approve` - Approve topic
- `POST /api/scripts/{id}/generate` - Create script
- `POST /api/scripts/{id}/update` - Human edit
- `GET /api/pipeline/status/{id}` - Check progress

### 6. **Pipeline Orchestrator** (`backend/pipeline/orchestrator.py`)
- State transitions (validated)
- Job creation & status tracking
- Async job queue management

## Data Flow: Topic → Script

```
User clicks "Generate Topics"
    ↓
POST /api/topics/generate
    ↓
MockLLMProvider.generate()
    ↓
Save 5 topics to DB (DISCOVERED state)
    ↓
User views topics list
    ↓
User clicks "Approve" on topic
    ↓
POST /api/topics/{id}/approve
    ↓
Topic status: DISCOVERED → APPROVED
    ↓
User clicks "Generate Script"
    ↓
POST /api/scripts/{id}/generate
    ↓
Create script record (GENERATING state)
    ↓
Background task calls LLM
    ↓
MockLLMProvider.generate(script_prompt)
    ↓
Save generated script to DB (DRAFTED state)
    ↓
User sees script in editor
    ↓
User clicks "Approve Script"
    ↓
POST /api/scripts/{id}/approve
    ↓
Script status: DRAFTED → APPROVED
```

## Mock Data (Testing)

MockLLMProvider returns hardcoded topics and scripts:

**Mock Topics:**
- "The Great Molasses Flood of 1919"
- "How the Printing Press Changed History"
- "The Mystery of the Voynich Manuscript"
- "The Lost City of Atlantis: Myths vs Facts"
- "How Penicillin Was Discovered by Accident"

**Mock Script Template:**
Generated for first topic with structure:
- Hook/intro
- Historical context
- Key facts with timestamps
- [VISUAL] markers for scenes

## Configuration

Environment variables (`.env` or `backend/core/config.py` defaults):

```env
APP_NAME=AI Documentary Studio
APP_VERSION=0.1.0
DEBUG=False

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173

LLM_PROVIDER=mock          # or "ollama"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Deployment (Development)

```bash
# Install dependencies
venv/Scripts/pip install -r backend/requirements.txt

# Run dev server with hot reload
venv/Scripts/python.exe backend/run.py

# Server listens on http://127.0.0.1:8000
```

## Testing API

```bash
# Generate topics
curl -X POST http://127.0.0.1:8000/api/topics/generate

# List topics
curl http://127.0.0.1:8000/api/topics | jq

# Approve first topic
TOPIC_ID=$(curl -s http://127.0.0.1:8000/api/topics | jq -r '.[0].id')
curl -X POST http://127.0.0.1:8000/api/topics/$TOPIC_ID/approve

# Generate script
curl -X POST http://127.0.0.1:8000/api/scripts/$TOPIC_ID/generate

# Check script status
curl http://127.0.0.1:8000/api/scripts/{script_id} | jq '.status'
```

## Dependencies

**Backend Core:**
- `fastapi==0.109.0` - HTTP framework
- `uvicorn[standard]==0.27.0` - ASGI server
- `pydantic>=2.8.0` - Data validation
- `pydantic-settings>=2.0.0` - Environment config

**Database:**
- `sqlalchemy==2.0.23` - ORM (future)
- `aiosqlite==0.19.0` - Async SQLite (future)

**LLM:**
- `httpx>=0.27.0` - Async HTTP (Ollama)
- `ollama>=0.3.0` - Ollama SDK (future)

**Utilities:**
- `python-dotenv==1.0.0` - .env loading

**Testing:**
- `pytest==7.4.3`
- `pytest-asyncio==0.21.1`

## Design Decisions

1. **Mock LLM First** - Validate flow without external dependency
2. **State Machine** - Deterministic pipeline (not prompt-chaotic)
3. **Async Background Jobs** - Non-blocking UI
4. **SQLite Local** - No server setup required
5. **Pydantic Models** - Type-safe API contracts
6. **Provider Pattern** - Swappable LLM backends

## Limitations (by Design)

- **No authentication** - Phase 2
- **No research** - Phase 2
- **No video rendering** - Phase 3
- **No YouTube upload** - Phase 4
- **No analytics** - Phase 5

## Next Phase (Phase 2)

- **Research module**: Web scraping + source storage
- **Fact extraction**: Multi-source consolidation
- **Research viewer UI**: Source sidebar + citations
- **Script integration**: Research → Script generation

---

**Phase 1 Status:** ✓ MVP Complete

**Total Build Time:** ~2 hours (database, models, LLM, API, orchestrator)

**Lines of Code:** ~800 (backend only, excluding dependencies)
