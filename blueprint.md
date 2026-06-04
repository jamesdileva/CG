🧱 AI DOCUMENTARY STUDIO — DEVELOPMENT BLUEPRINT

0. SYSTEM OVERVIEW (FINAL FORM)
Electron (React UI)
       ↓ HTTP (localhost)
Python FastAPI Backend
       ↓
Pipeline Orchestrator
       ↓
LLM Layer (Ollama / OpenAI)
       ↓
SQLite + File System
       ↓
FFmpeg + TTS + Assets

1. BACKEND ARCHITECTURE (PYTHON)
📦 Core Stack
FastAPI (API layer)
Pydantic (data models)
SQLite (state + persistence)
httpx (external requests)
trafilatura (clean scraping)
ollama / openai SDK
ffmpeg-python
asyncio (pipeline jobs)

📁 Backend Folder Structure (REAL)
backend/
├── main.py                 # FastAPI entrypoint
├── api/
│   ├── topics.py
│   ├── research.py
│   ├── scripts.py
│   ├── pipeline.py
│   ├── videos.py
│   ├── analytics.py
│
├── core/
│   ├── database.py
│   ├── config.py
│   ├── logger.py
│
├── pipeline/
│   ├── orchestrator.py
│   ├── states.py
│   ├── jobs.py
│   ├── transitions.py
│
├── llm/
│   ├── provider.py
│   ├── ollama.py
│   ├── openai.py
│   ├── prompts/
│   │   ├── topic_generation.txt
│   │   ├── research.txt
│   │   ├── script.txt
│   │   ├── fact_check.txt
│
├── research/
│   ├── scraper.py
│   ├── sources.py
│   ├── extractor.py
│   ├── ranking.py
│
├── video/
│   ├── scenes.py
│   ├── renderer.py
│   ├── ffmpeg_builder.py
│   ├── tts.py
│
├── assets/
│   ├── manager.py
│
├── models/
│   ├── topics.py
│   ├── scripts.py
│   ├── videos.py
│   ├── jobs.py
│
└── utils/
   ├── embeddings.py
   ├── similarity.py

2. API CONTRACTS (FRONTEND ↔ BACKEND)
This is CRITICAL for Electron design.

📌 TOPICS
Generate Topics
POST /api/topics/generate
Response:
{
 "topics": [
   {
     "id": "uuid",
     "title": "The Great Molasses Flood",
     "score": 92,
     "category": "Disaster History",
     "sources_available": true
   }
 ]
}

Get Topics List
GET /api/topics

Approve Topic
POST /api/topics/{id}/approve

Reject Topic
POST /api/topics/{id}/reject

📌 RESEARCH
Start Research
POST /api/research/start/{topic_id}

Get Research
GET /api/research/{topic_id}
Returns:
{
 "sources": [],
 "facts": [],
 "timeline": [],
 "conflicts": []
}

📌 SCRIPT
Generate Script
POST /api/scripts/generate/{topic_id}

Get Script
GET /api/scripts/{topic_id}

Update Script (Human Edit)
POST /api/scripts/{script_id}/update

Approve Script
POST /api/scripts/{script_id}/approve

📌 VIDEO
Start Render
POST /api/videos/render/{topic_id}

Get Video Status
GET /api/videos/{topic_id}

📌 PIPELINE CONTROL
Trigger Full Pipeline
POST /api/pipeline/run
Body:
{
 "topic_id": "uuid",
 "mode": "manual"
}

Get Pipeline Status
GET /api/pipeline/status/{topic_id}

3. PIPELINE ORCHESTRATOR (CORE ENGINE)
This is the brain.
class PipelineOrchestrator:

   async def run_topic_pipeline(self, topic_id):
       await self.transition(topic_id, "RESEARCHING")
       research = await self.research(topic_id)

       await self.transition(topic_id, "SCRIPT_DRAFTED")
       script = await self.generate_script(topic_id, research)

       return script

STATE MACHINE
VALID_TRANSITIONS = {
   "DISCOVERED": ["APPROVED"],
   "APPROVED": ["RESEARCHING"],
   "RESEARCHING": ["RESEARCH_COMPLETE"],
   "RESEARCH_COMPLETE": ["SCRIPT_DRAFTED"],
   "SCRIPT_DRAFTED": ["SCRIPT_APPROVED"],
   "SCRIPT_APPROVED": ["VIDEO_RENDERED"]
}

4. LLM LAYER (IMPORTANT DESIGN)
We never call models directly.
We use abstraction:
class LLMProvider:
   def generate(self, prompt: str) -> str:
       pass

Ollama Implementation
class OllamaProvider(LLMProvider):
   def generate(self, prompt):
       return ollama.chat(model="llama3", messages=[...])

OpenAI fallback
Same interface.

Prompt Templates
Example:
You are a documentary researcher.

Extract factual information only.

Return:
- facts
- timeline
- key entities
- sources summary

5. ELECTRON FRONTEND (REAL STRUCTURE)

📁 Renderer Structure
renderer/src/
├── pages/
│   ├── Dashboard.tsx
│   ├── Topics.tsx
│   ├── Research.tsx
│   ├── ScriptEditor.tsx
│   ├── Production.tsx
│   ├── Publish.tsx
│   ├── Analytics.tsx
│
├── components/
│   ├── TopicCard.tsx
│   ├── ScriptBlock.tsx
│   ├── SourceViewer.tsx
│   ├── VideoTimeline.tsx
│   ├── PipelineStatus.tsx
│
├── api/
│   ├── client.ts
│   ├── topics.ts
│   ├── scripts.ts
│   ├── pipeline.ts
│
├── store/
│   ├── topicStore.ts
│   ├── scriptStore.ts
│
└── utils/
   ├── formatters.ts

6. ELECTRON MAIN PROCESS
electron/
├── main.js
├── preload.js
├── windowManager.js

Main Window
Single window app:
createWindow({
 width: 1400,
 height: 900,
 webPreferences: {
   preload: preload.js
 }
})

IPC Bridge (optional but clean)
contextBridge.exposeInMainWorld("api", {
 topics: topicsAPI,
 scripts: scriptsAPI,
 pipeline: pipelineAPI
})

7. FILE SYSTEM LAYOUT (LOCAL STORAGE)
data/
├── projects/
│   ├── {topic_id}/
│   │   ├── research.json
│   │   ├── script.txt
│   │   ├── scenes/
│   │   ├── audio/
│   │   ├── video.mp4
│   │   ├── thumbnails/

8. JOB SYSTEM (VERY IMPORTANT)
We avoid blocking UI.
class Job:
   id
   type
   status
   payload

Job Types
topic_generation
research
script_generation
video_render
upload

Worker Loop
while True:
   job = get_next_job()
   process(job)

9. EMBEDDINGS + DEDUP SYSTEM
This is your anti-repeat engine.
def is_duplicate(topic_embedding, existing_embeddings):
   return cosine_similarity > 0.90

10. MVP BUILD PLAN (REALISTIC SPRINTS)

🟢 SPRINT 1 — CORE PIPELINE (WEEK 1–2)
Build:
Electron shell
Topics screen
Script editor screen
FastAPI backend
SQLite
Ollama integration
Output:
Generate topics
Select topic
Generate script
Edit + approve script
✔ MVP VALUE ACHIEVED HERE

🟡 SPRINT 2 — RESEARCH SYSTEM (WEEK 3)
Web scraping
Source storage
Fact extraction
Research UI

🔵 SPRINT 3 — VIDEO ENGINE (WEEK 4–5)
Scene splitting
TTS integration
FFmpeg rendering
Asset pipeline

🟣 SPRINT 4 — YOUTUBE INTEGRATION (WEEK 6)
Upload API
Metadata generator
Thumbnail system

🔴 SPRINT 5 — ANALYTICS LOOP (WEEK 7)
Pull YouTube analytics
Feed back into scoring
Improve topic ranking

11. MVP DEFINITION (WHAT “DONE” MEANS)
MVP is complete when:
✔ You can generate 20 topics
 ✔ Select one
 ✔ Generate research + script
 ✔ Edit script
 ✔ Render a video locally
 ✔ Export MP4
Anything beyond this = expansion

12. KEY ARCHITECTURAL INSIGHT
This system only works if:
The pipeline is deterministic and state-driven, NOT prompt-chaotic.
So everything revolves around:
Topic → State → Job → Output → Next State
NOT:
random prompts everywhere

