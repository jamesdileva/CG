"""FastAPI Backend for AI Documentary Studio"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database on startup
from backend.core.database import init_db
from backend.llm import init_llm

app = FastAPI(
    title="AI Documentary Studio API",
    description="Backend for local-first documentary production",
    version="0.1.0"
)

# Enable CORS for Electron frontend (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup"""
    logger.info("Starting up...")
    init_db()
    await init_llm()
    logger.info("Startup complete")


@app.get("/")
async def root():
    return {
        "message": "AI Documentary Studio API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Import and include routers
from backend.api import topics, scripts, pipeline

app.include_router(topics.router)
app.include_router(scripts.router)
app.include_router(pipeline.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
