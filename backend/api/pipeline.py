"""Pipeline control endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.core.database import get_db

logger = None
router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
orchestrator = PipelineOrchestrator()


class PipelineRunRequest(BaseModel):
    topic_id: str
    mode: str = "manual"


@router.get("/status/{topic_id}")
async def get_pipeline_status(topic_id: str):
    """Get pipeline status for a topic"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get topic status
        cursor.execute("SELECT status FROM topics WHERE id = ?", (topic_id,))
        topic_row = cursor.fetchone()
        if not topic_row:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get associated scripts
        cursor.execute(
            "SELECT COUNT(*) as count, MAX(updated_at) as latest FROM scripts WHERE topic_id = ?",
            (topic_id,),
        )
        script_row = cursor.fetchone()

        return {
            "topic_id": topic_id,
            "topic_status": topic_row["status"],
            "scripts_count": script_row["count"],
            "latest_update": script_row["latest"],
        }


@router.post("/run")
async def run_pipeline(request: PipelineRunRequest):
    """Trigger pipeline execution for a topic"""
    # Verify topic exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (request.topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

    # Create job to generate script
    job_id = await orchestrator.create_job(
        job_type="script_generation",
        topic_id=request.topic_id,
        payload={"mode": request.mode},
    )

    return {
        "message": "Pipeline started",
        "topic_id": request.topic_id,
        "job_id": job_id,
    }


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a pipeline job"""
    status = await orchestrator.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return status
