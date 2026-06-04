# **📄 SYSTEM ARCHITECTURE DOCUMENT**

## **AI DOCUMENTARY CONTENT STUDIO (Desktop App)**

---

# **1\. 🧠 PRODUCT DEFINITION**

A local-first desktop application that:

* Generates and ranks documentary topics  
* Performs multi-source research with citations  
* Produces structured scripts (human-approved)  
* Generates narration \+ visuals  
* Assembles long-form YouTube videos  
* Extracts Shorts automatically  
* Uploads to YouTube (optional approval step)  
* Learns from analytics to improve future topics

---

# **2\. 🧩 CORE DESIGN PRINCIPLES**

### **1\. Human-in-the-loop by default**

Nothing publishes without approval.

### **2\. Pipeline-based architecture**

Everything is a state transition, not a “chat prompt”.

### **3\. Local-first**

Runs on your machine:

* SQLite  
* Local file storage  
* Optional cloud APIs (YouTube/OpenAI)

### **4\. Replaceable AI providers**

Ollama or OpenAI interchangeable.

### **5\. Deterministic workflow**

Same input → same structured pipeline outputs.

---

# **3\. 🏗️ HIGH-LEVEL SYSTEM ARCHITECTURE**

           ┌──────────────────────────┐  
           │    ELECTRON FRONTEND                      │  
           │ (UI Screens 1–7)                                      │  
           └──────────┬───────────────┘  
                      │ IPC / API Calls  
                      ▼  
           ┌──────────────────────────┐  
           │      PYTHON BACKEND                            │  
           │   Pipeline Orchestrator                               │  
           └──────────┬───────────────┘  
                      │  
     ┌────────────────┼────────────────┐  
     ▼                ▼                ▼  
┌──────────┐   ┌──────────────┐  ┌──────────────┐  
│ SQLite DB    │ LLM Layer         File System  │  
│                 Ollama/OpenAI  │ assets/video │  
└──────────┘   └──────────────┘  └──────────────┘  
                      │  
                      ▼  
             ┌──────────────────┐  
             │ FFmpeg Renderer                 │  
             └──────────────────┘  
---

# **4\. 🔁 PIPELINE STATE MACHINE**

Every topic moves through fixed states:

DISCOVERED  
→ RANKED  
→ APPROVED  
→ RESEARCHING  
→ RESEARCH\_COMPLETE  
→ SCRIPT\_DRAFTED  
→ SCRIPT\_APPROVED  
→ ASSETS\_GENERATED  
→ VIDEO\_RENDERED  
→ THUMBNAIL\_SELECTED  
→ READY\_TO\_UPLOAD  
→ UPLOADED  
→ ANALYTICS\_COLLECTED  
→ ARCHIVED  
---

# **5\. 🖥️ ELECTRON WINDOW STRUCTURE**

## **Main Window Layout**

Single-window app with route-based views:

APP  
├── Dashboard  
├── Topics  
├── Research Viewer  
├── Script Editor  
├── Production Studio  
├── Thumbnail & Title  
├── Publish Manager  
├── Analytics  
└── Settings  
---

## **Screen Responsibilities**

### **1\. Dashboard**

* Generate topics  
* Resume pipeline  
* Show system status

---

### **2\. Topics Screen**

* Rank 20–100 topics  
* Approve/reject  
* Deduplicate alerts

---

### **3\. Research Viewer**

* Sources list  
* Extracted facts  
* Timeline view  
* Citations tracking

---

### **4\. Script Editor**

* Editable structured script  
* AI rewrite per section  
* Approval gate

---

### **5\. Production Studio**

* Scene-by-scene rendering  
* Voice \+ image pairing  
* Timeline preview

---

### **6\. Thumbnail & Title**

* Title generator  
* Thumbnail selection  
* CTR optimization tools

---

### **7\. Publish Manager**

* YouTube upload  
* Metadata review  
* Scheduling

---

### **8\. Analytics**

* Performance tracking  
* Topic scoring feedback loop

---

# **6\. 🗄️ DATABASE SCHEMA (SQLite)**

---

## **topics**

CREATE TABLE topics (  
   id TEXT PRIMARY KEY,  
   title TEXT,  
   category TEXT,

   status TEXT,

   interest\_score REAL,  
   uniqueness\_score REAL,  
   source\_score REAL,

   embedding BLOB,

   created\_at TEXT,  
   updated\_at TEXT,  
   published\_at TEXT  
);  
---

## **topic\_relationships**

CREATE TABLE topic\_relationships (  
   id TEXT PRIMARY KEY,  
   topic\_id TEXT,  
   related\_topic\_id TEXT,  
   relationship\_type TEXT  
);  
---

## **sources**

CREATE TABLE sources (  
   id TEXT PRIMARY KEY,  
   topic\_id TEXT,

   url TEXT,  
   title TEXT,  
   content TEXT,

   credibility\_score REAL,  
   created\_at TEXT  
);  
---

## **facts**

CREATE TABLE facts (  
   id TEXT PRIMARY KEY,  
   topic\_id TEXT,

   fact TEXT,  
   source\_id TEXT,  
   verified INTEGER  
);  
---

## **scripts**

CREATE TABLE scripts (  
   id TEXT PRIMARY KEY,  
   topic\_id TEXT,

   version INTEGER,  
   script TEXT,

   status TEXT,

   created\_at TEXT  
);  
---

## **scenes**

CREATE TABLE scenes (  
   id TEXT PRIMARY KEY,  
   script\_id TEXT,

   order\_index INTEGER,  
   text TEXT,

   image\_path TEXT,  
   audio\_path TEXT,  
   duration REAL  
);  
---

## **videos**

CREATE TABLE videos (  
   id TEXT PRIMARY KEY,  
   topic\_id TEXT,

   file\_path TEXT,  
   youtube\_id TEXT,

   status TEXT,

   created\_at TEXT  
);  
---

## **assets**

CREATE TABLE assets (  
   id TEXT PRIMARY KEY,

   type TEXT, \-- image, audio, thumbnail

   file\_path TEXT,

   topic\_id TEXT,  
   scene\_id TEXT  
);  
---

## **analytics**

CREATE TABLE analytics (  
   id TEXT PRIMARY KEY,  
   video\_id TEXT,

   views INTEGER,  
   watch\_time REAL,  
   ctr REAL,

   captured\_at TEXT  
);  
---

## **jobs (pipeline control)**

CREATE TABLE jobs (  
   id TEXT PRIMARY KEY,

   type TEXT, \-- research, script, render, upload

   topic\_id TEXT,

   status TEXT,

   payload TEXT,

   created\_at TEXT,  
   updated\_at TEXT  
);  
---

# **7\. 🧠 MVP BUILD PLAN (IMPORTANT)**

We do NOT build everything at once.

---
📚 PHASE ARTIFACT SYSTEM (IMPORTANT)

Every sprint is required to generate a living documentation package.

This turns the project into:

“A self-documenting AI production system”

📦 PHASE OUTPUT STRUCTURE

After each sprint, you generate a folder like:

docs/
└── phase-01-core-pipeline/
    ├── overview.md
    ├── architecture.md
    ├── api-reference.md
    ├── database-schema.md
    ├── code-examples.md
    ├── prompts.md
    ├── lessons-learned.md

# **🟢 PHASE 1 — CORE PIPELINE (MVP)**

### **Goal:**

Get from topic → script → approved script

### **Build:**

* Electron UI (3 screens only)  
  * Dashboard  
  * Topics  
  * Script Editor  
* Python backend:  
  * Topic generation  
  * Research stub (mock or simple scraping)  
  * Script generation (Ollama OK)  
* SQLite DB

### **Output:**

* Approved script saved locally

---

# **🟡 PHASE 2 — RESEARCH SYSTEM**

* Multi-source scraping  
* Fact extraction  
* Source storage  
* Research Viewer UI

---

# **🔵 PHASE 3 — VIDEO PIPELINE**

* Scene splitting  
* FFmpeg video generation  
* Voice generation (TTS)  
* Asset manager

---

# **🟣 PHASE 4 — YOUTUBE INTEGRATION**

* Upload automation  
* Metadata builder  
* Thumbnail selection

---

# **🔴 PHASE 5 — ANALYTICS LOOP**

* YouTube API ingestion  
* Topic scoring adjustment  
* Auto ranking system

---

# **8\. 🧩 ELECTRON ARCHITECTURE**

## **Tech Choice**

* Electron (UI)  
* React (renderer)  
* Python backend (local server)  
* IPC bridge (REST or WebSocket)

---

## **Folder Structure**

app/  
├── electron/  
│   ├── main.js  
│   ├── preload.js  
│  
├── renderer/  
│   ├── src/  
│   │   ├── pages/  
│   │   ├── components/  
│   │   ├── store/  
│   │   ├── api/  
│  
├── backend/  
│   ├── app.py  
│   ├── pipeline/  
│   ├── llm/  
│   ├── research/  
│   ├── video/  
│  
├── database/  
│   ├── schema.sql  
│   ├── db.py  
│  
├── assets/  
│   ├── images/  
│   ├── audio/  
│   ├── videos/  
│  
└── config/  
   ├── settings.json  
---

## **IPC Flow**

Electron UI  
  ↓  
HTTP request (localhost)  
  ↓  
Python backend API  
  ↓  
SQLite \+ LLM \+ FFmpeg  
  ↓  
Return result  
  ↓  
UI updates  
---

# **9\. 🔑 KEY DESIGN INSIGHT**

This entire system is NOT:

“AI generating YouTube videos”

It is:

“A structured documentary production pipeline with AI assistance”

That distinction is what keeps it:

* scalable  
* monetizable  
* controllable  
* not spammy  
* not hallucination-prone

---

# **10\. 🚀 WHAT WE BUILD FIRST (VERY IMPORTANT)**

If we start correctly:

### **FIRST BUILD THIS:**

### **1\. Topic Generator (ranked list)**

### **2\. Script Editor (approval UI)**

### **3\. SQLite storage**

### **4\. Basic LLM integration (Ollama)**

That alone already gives value.

Everything else is expansion.

