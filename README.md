# AI Documentary Studio

A **local-first desktop application** for generating, researching, scripting, and producing long-form YouTube documentaries with AI assistance.

## Vision

Transform topics into fully-researched, scripted, and produced documentaries through an intelligent state-driven pipeline. Every documentary moves through predictable stages with human approval gates and feedback loops.

## Tech Stack

- **Frontend**: Electron + React (TypeScript)
- **Backend**: Python FastAPI
- **Database**: SQLite (local, no cloud required)
- **LLM**: Ollama (llama3.1, 4096 token context)
- **Video**: FFmpeg + TTS (edge-tts or espeak)
- **API**: HTTP (localhost communication)

## Project Structure

```
c:\Users\j\CG/
├── backend/              # Python FastAPI backend
├── renderer/             # Electron + React frontend
├── database/             # SQLite schema and migrations
├── data/                 # Runtime data (projects, DB, assets)
├── docs/                 # Phase documentation packages
└── config/               # Configuration files
```

## Getting Started

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

## Quick Start

### Backend
```bash
source venv/Scripts/activate  # Windows
pip install -r backend/requirements.txt
python backend/run.py
# FastAPI running on http://localhost:8000
```

### Frontend
```bash
cd renderer
npm install
npm run electron-dev
# Electron window opens, connected to backend
```

## Roadmap

### Phase 1: Core Pipeline ✅ (In Progress)
- Topic generation (LLM prompts)
- Script generation (from topics)
- Script editing & approval
- Database schema & state management

### Phase 2: Research System
- Web scraping (trafilatura)
- Source credibility ranking
- Fact extraction & deduplication

### Phase 3: Video Pipeline
- Scene splitting from script
- TTS audio generation
- FFmpeg rendering to MP4

### Phase 4: YouTube Integration
- OAuth authentication
- Metadata management
- Upload to YouTube

### Phase 5: Analytics Loop
- Pull YouTube analytics
- Feedback loop for topic ranking
- Auto-improve scoring

## Key Concepts

### State Machine
Every topic follows a deterministic state sequence:
```
DISCOVERED → APPROVED → RESEARCHING → RESEARCH_COMPLETE
→ SCRIPT_DRAFTED → SCRIPT_APPROVED → ASSETS_GENERATED
→ VIDEO_RENDERED → THUMBNAIL_SELECTED → READY_TO_UPLOAD
→ UPLOADED → ANALYTICS_COLLECTED → ARCHIVED
```

### Approval Gates
Key decisions require human approval:
- ✅ Topic selection (auto-generate, human picks)
- ✅ Script approval (generate, edit, approve)
- ✅ Video quality (preview, approve, upload)

### Async Jobs
Long-running tasks (research, rendering) use a job queue:
- Jobs table tracks status (PENDING, RUNNING, COMPLETE, FAILED)
- Frontend polls for progress
- Errors captured for debugging

## Configuration

Copy `.env.example` to `.env` and adjust:
```bash
cp .env.example .env
```

Key settings:
- `OLLAMA_BASE_URL`: Ollama server (default: localhost:11434)
- `OLLAMA_MODEL`: Model name (default: llama2)
- `DATABASE_URL`: SQLite path

## Development
# Terminal 1: Backend**
cd C:\Users\j\CG
venv\Scripts\activate
python backend\run.py
**
# Terminal 2: Frontend (Electron)**
cd C:\Users\j\CG\renderer
npm run electron-dev
### Running Tests

**Backend**:
```bash
cd backend
pytest tests/
```

**Frontend**:
```bash
cd renderer
npm run test
```

### Adding Features

1. Define API endpoint in `backend/api/`
2. Add database schema changes to `database/schema.sql`
3. Create React component in `renderer/src/pages/` or `components/`
4. Add HTTP client method in `renderer/src/api/`
5. Update Zustand store in `renderer/src/store/`

### Database Migrations

SQLite schema is version-controlled in `database/schema.sql`. For changes:
1. Update schema.sql
2. Increment version in migrations.py
3. Run migrations on startup

## Documentation

Each phase includes a documentation package in `docs/`:
- `overview.md` — What was built and why
- `architecture.md` — Component diagrams and data flow
- `api-reference.md` — All endpoints for this phase
- `database-schema.md` — Table definitions
- `code-examples.md` — How-to snippets
- `prompts.md` — LLM prompt templates
- `lessons-learned.md` — Gotchas and design decisions

## Troubleshooting

### Backend fails to start
- Ensure Python 3.9+ and venv is activated
- Check `BACKEND_PORT` (default 8000) isn't in use
- Verify `DATABASE_URL` path exists

### Frontend won't connect to backend
- Ensure backend is running on localhost:8000
- Check browser console for CORS errors
- Verify firewall allows localhost traffic

### Ollama not responding
- Install Ollama from ollama.ai
- Start Ollama: `ollama serve`
- Pull model: `ollama pull llama2`
- Verify running: `curl http://localhost:11434/api/tags`

## License

[Your License Here]

## Support

Questions? Issues? Check the docs/ folder or open an issue.
