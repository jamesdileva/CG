# Development Setup Guide

Complete setup instructions for AI Documentary Studio.

## Prerequisites

### System Requirements
- **Python**: 3.9+ (recommended: 3.11 LTS)
- **Node.js**: 18+ (comes with npm)
- **Ollama**: Latest version (for LLM)
- **FFmpeg**: For video processing
- **Git**: For version control

### Installation

#### Python (Windows)
1. Download from https://www.python.org/
2. Run installer, select "Add Python to PATH"
3. Verify: `python --version`

#### Node.js (Windows)
1. Download from https://nodejs.org/ (LTS recommended)
2. Run installer
3. Verify: `node --version` and `npm --version`

#### Ollama (Windows)
1. Download from https://ollama.ai/
2. Run installer
3. Start Ollama
4. Pull model: `ollama pull llama2`
5. Verify: `curl http://localhost:11434/api/tags`

#### FFmpeg (Windows)
1. Download from https://ffmpeg.org/download.html
2. Extract to a directory (e.g., `C:\tools\ffmpeg`)
3. Add to PATH or reference in `.env`
4. Verify: `ffmpeg -version`

## Backend Setup

### Step 1: Create Python Virtual Environment

```bash
cd c:\Users\j\CG
python -m venv venv
# Activate (Windows)
venv\Scripts\activate
# Or (Git Bash / WSL)
source venv/Scripts/activate
```

### Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

Expected output: "Successfully installed [packages]"

### Step 3: Create `.env` File

```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings to verify:
```
BACKEND_URL=http://localhost:8000
DATABASE_URL=sqlite:///./data/db/studio.db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
LOG_LEVEL=INFO
```

### Step 4: Initialize Database

```bash
# The database will auto-initialize on first backend run
# Or manually initialize with:
python -c "from backend.core.database import init_db; init_db()"
```

### Step 5: Run Backend

```bash
python backend/run.py
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

### Step 6: Test Backend

In another terminal:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

## Frontend Setup

### Step 1: Install Node Dependencies

```bash
cd renderer
npm install
```

This creates `node_modules/` with Electron, React, TypeScript, etc.

### Step 2: Build Configuration

TypeScript config is already set up:
- `tsconfig.json` — Main config
- `vite.config.ts` — Build config
- `package.json` — Scripts and deps

### Step 3: Run Development Server

**Option A: Vite Dev Server Only** (for web testing)
```bash
RUN FRONTEND

cd renderer
npm run dev
# Open http://localhost:5173 in browser
```

**Option B: RUN BACK END AND DO THIS BELOW Electron + Dev Server** (full desktop app)
```bash
venv\Scripts\activate
cd renderer
npm run electron-dev
# Electron window opens, connected to dev server
```

```
# Terminal 1: Backend**
cd C:\Users\j\CG
venv\Scripts\activate
python backend\run.py
**
# Terminal 2: Frontend (Electron)**
cd C:\Users\j\CG\renderer
npm run electron-dev
```

**Option C: Build for Production**
```bash
cd renderer
npm run build
npm run electron
```

### Step 4: Test Frontend

In Electron dev tools (Ctrl+Shift+I):
- Check console for errors
- Network tab shows API calls to backend
- Verify window title is "AI Documentary Studio"

## Full Integration Test

### Prerequisites
1. Backend running: `python backend/run.py`
2. Ollama running with llama2 pulled
3. FFmpeg available on PATH

### Test Workflow

1. **Start Backend** (Terminal 1)
   ```bash
   python backend/run.py
   ```

2. **Start Frontend** (Terminal 2)
   ```bash
   cd renderer
   npm run electron-dev
   ```

3. **Test in Electron Window**
   - App should show "AI Documentary Studio"
   - Button click should increment counter
   - Check DevTools Network tab (Ctrl+Shift+I):
     - Open DevTools
     - Network tab
     - Click button to see if any API calls

4. **Test Backend** (Terminal 3)
   ```bash
   curl http://localhost:8000/
   # Returns: {"message":"AI Documentary Studio API","status":"running"}
   ```

## Database Management

### Initialize Fresh

```bash
# Delete old database
rm data/db/studio.db

# Restart backend (auto-initializes)
python backend/run.py
```

### View Database

```bash
# Install sqlite3 CLI (already included on Windows)
sqlite3 data/db/studio.db

# Common queries
sqlite> SELECT * FROM topics;
sqlite> SELECT * FROM scripts;
sqlite> .tables
sqlite> .quit
```

## Environment Variables

### Required
- `BACKEND_URL` — Where backend runs
- `DATABASE_URL` — SQLite file path
- `OLLAMA_BASE_URL` — Ollama server URL

### Optional (defaults provided)
- `OLLAMA_MODEL` — Default: llama2
- `LOG_LEVEL` — Default: INFO
- `FFMPEG_PATH` — Default: system PATH
- `RESEARCH_MAX_SOURCES` — Default: 50

## Troubleshooting

### "venv\Scripts\activate: command not found"
- You're in Git Bash, use: `source venv/Scripts/activate`
- Or use Windows Command Prompt with `venv\Scripts\activate.bat`

### "ModuleNotFoundError: No module named 'fastapi'"
- Activate venv: `source venv/Scripts/activate`
- Install: `pip install -r backend/requirements.txt`

### "Ollama is not running"
- Start Ollama application
- Verify: `curl http://localhost:11434/api/tags`

### "Connection refused on localhost:8000"
- Is backend running? Check terminal output
- Is port 8000 in use? `netstat -ano | findstr 8000`
- Try different port: Edit `BACKEND_URL` in `.env`

### "Electron window blank"
- Check DevTools (Ctrl+Shift+I)
- Check console for errors
- Verify backend is running
- Try: `npm run build && npm run electron`

## Next Steps

1. ✅ Backend and frontend running?
2. 📖 Read [Phase 1 Plan](docs/phase-01-core-pipeline/overview.md) (coming soon)
3. 🔧 Start Phase 1 implementation
4. 📝 Add features and run tests

## Development Workflow

### Adding a Backend Endpoint
1. Create file in `backend/api/` (e.g., `topics.py`)
2. Define routes with FastAPI decorators
3. Test with curl or Postman
4. Document in phase docs

### Adding a React Component
1. Create `.tsx` file in `src/pages/` or `src/components/`
2. Import in `App.tsx` or router
3. Call backend API using `src/api/client.ts`
4. Update Zustand store if needed

### Running Tests
```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd renderer
npm run test
```

## Additional Resources

- Electron: https://www.electronjs.org/docs
- React: https://react.dev
- FastAPI: https://fastapi.tiangolo.com
- SQLite: https://www.sqlite.org/docs.html
- Ollama: https://github.com/ollama/ollama

## Support

Stuck? Check:
1. This guide (DEVELOPMENT.md)
2. README.md for overview
3. architecture.md in docs/
4. backend/run.py and vite.config.ts for defaults
