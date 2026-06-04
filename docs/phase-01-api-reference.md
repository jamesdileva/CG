**# Phase 1 Backend — API Reference**

## Running the Backend

```bash
cd /c/Users/j/CG
venv/Scripts/python.exe backend/run.py
```

Server runs on `http://127.0.0.1:8000`

---

## API Endpoints

### Topics

#### `POST /api/topics/generate`
Generate new documentary topics (mock data for now)

**Response:**
```json
{
  "message": "Topic generation started",
  "status": "processing"
}
```

#### `GET /api/topics`
List all topics

**Query params:**
- `status` - filter by status (DISCOVERED, APPROVED, etc.)
- `limit` - max results (default 50)

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "The Great Molasses Flood of 1919",
    "description": "",
    "status": "DISCOVERED",
    "created_at": "2026-06-04T...",
    "updated_at": "2026-06-04T...",
    "approved_at": null,
    "embedding": null
  }
]
```

#### `GET /api/topics/{topic_id}`
Get a specific topic

#### `POST /api/topics/{topic_id}/approve`
Approve a topic (transitions DISCOVERED → APPROVED)

#### `POST /api/topics/{topic_id}/reject`
Reject a topic (deletes if in DISCOVERED state)

---

### Scripts

#### `POST /api/scripts/{topic_id}/generate`
Generate a script for an approved topic

**Response:**
```json
{
  "script_id": "uuid",
  "status": "generating"
}
```

#### `GET /api/scripts/{script_id}`
Get a specific script

**Response:**
```json
{
  "id": "uuid",
  "topic_id": "uuid",
  "content": "Generated script text...",
  "status": "DRAFTED",
  "version": 1,
  "created_at": "2026-06-04T...",
  "updated_at": "2026-06-04T...",
  "approved_at": null
}
```

#### `GET /api/scripts/topic/{topic_id}`
Get all scripts for a topic (newest first)

#### `POST /api/scripts/{script_id}/update`
Update script content (human edit)

**Body:**
```json
{
  "content": "Updated script text...",
  "status": "DRAFTED"
}
```

#### `POST /api/scripts/{script_id}/approve`
Approve a script (transitions DRAFTED → APPROVED)

---

### Pipeline Control

#### `GET /api/pipeline/status/{topic_id}`
Get overall pipeline status

**Response:**
```json
{
  "topic_id": "uuid",
  "topic_status": "APPROVED",
  "scripts_count": 1,
  "latest_update": "2026-06-04T..."
}
```

#### `POST /api/pipeline/run`
Trigger full pipeline (advanced, not used in Phase 1)

**Body:**
```json
{
  "topic_id": "uuid",
  "mode": "manual"
}
```

#### `GET /api/pipeline/job/{job_id}`
Get job status

---

## Database

SQLite database at `data/studio.db`

**Tables:**
- `topics` - documentary topics
- `scripts` - generated scripts
- `jobs` - async job queue
- `research_sources` - (Phase 2) web sources
- `research_facts` - (Phase 2) extracted facts
- `videos` - (Phase 3) rendered videos
- `youtube_uploads` - (Phase 4) YouTube metadata
- `analytics` - (Phase 5) YouTube stats

---

## LLM Configuration

Set via environment variable or `.env`:

```env
LLM_PROVIDER=mock     # or "ollama"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**Providers:**
- `mock` - Returns synthetic data (current)
- `ollama` - Local Ollama server (when available)
- `openai` - (future) OpenAI API

---

## Testing Flow

```bash
# Generate 5 topics
curl -X POST http://127.0.0.1:8000/api/topics/generate

# List topics
curl http://127.0.0.1:8000/api/topics

# Approve first topic
TOPIC_ID=$(curl -s http://127.0.0.1:8000/api/topics | jq -r '.[0].id')
curl -X POST http://127.0.0.1:8000/api/topics/$TOPIC_ID/approve

# Generate script for topic
curl -X POST http://127.0.0.1:8000/api/scripts/$TOPIC_ID/generate

# Check script
curl http://127.0.0.1:8000/api/scripts/{script_id}
```

---

## Files Created

**Core:**
- `backend/core/database.py` - SQLite connection & initialization
- `backend/core/config.py` - Configuration management
- `backend/core/logger.py` - (placeholder) Logging setup

**Models:**
- `backend/models/topics.py` - Pydantic models for topics
- `backend/models/scripts.py` - Pydantic models for scripts
- `backend/models/jobs.py` - Pydantic models for async jobs

**LLM Layer:**
- `backend/llm/provider.py` - Base provider interface
- `backend/llm/mock.py` - Mock LLM (current)
- `backend/llm/ollama.py` - Ollama provider
- `backend/llm/__init__.py` - Provider factory

**API:**
- `backend/api/topics.py` - Topic endpoints
- `backend/api/scripts.py` - Script endpoints
- `backend/api/pipeline.py` - Pipeline control endpoints

**Pipeline:**
- `backend/pipeline/orchestrator.py` - State machine & job queue

**Main:**
- `backend/main.py` - FastAPI app setup
- `backend/run.py` - Development runner

---

## Next: Phase 2

- Research system (web scraping)
- Source storage & fact extraction
- Research UI
- Integration with topics workflow
