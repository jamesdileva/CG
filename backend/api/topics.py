"""Topics API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import uuid
import json
import logging
from backend.core.database import get_db
from backend.models.topics import TopicCreate, TopicResponse, TopicUpdate
from backend.llm import get_llm
from backend.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/topics", tags=["topics"])
orchestrator = PipelineOrchestrator()

# Topic generation prompt template
TOPIC_GENERATION_PROMPT = """Generate 5 unique, compelling documentary topics that would work well for long-form YouTube content.
Each topic should:
- Be historically significant or have educational value
- Have readily available sources
- Be interesting to a general audience
- Not be overdone on YouTube

Format your response as a JSON array with objects containing "title" and "description" fields.
Example:
[
  {"title": "The Great Molasses Flood of 1919", "description": "..."},
  ...
]
"""


async def generate_topics_background(num_topics: int = 5):
    """Background task to generate topics using LLM"""
    try:
        llm = get_llm()
        response = await llm.generate(TOPIC_GENERATION_PROMPT)

        # Parse response
        topics_data = json.loads(response)
        if not isinstance(topics_data, list):
            topics_data = [topics_data]

        # Save to database
        with get_db() as conn:
            cursor = conn.cursor()
            for topic_data in topics_data[:num_topics]:
                topic_id = str(uuid.uuid4())
                cursor.execute(
                    """INSERT INTO topics (id, title, description, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        topic_id,
                        topic_data.get("title", "Untitled"),
                        topic_data.get("description", ""),
                        "DISCOVERED",
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat(),
                    ),
                )
            conn.commit()

        logger.info(f"Generated {len(topics_data)} topics")
    except Exception as e:
        logger.error(f"Failed to generate topics: {e}")


@router.post("/generate")
async def generate_topics(num_topics: int = 5, background_tasks: BackgroundTasks = None):
    """Generate new documentary topics"""
    if background_tasks:
        background_tasks.add_task(generate_topics_background, num_topics)
        return {"message": "Topic generation started", "status": "processing"}
    else:
        await generate_topics_background(num_topics)
        return {"message": "Topics generated successfully"}


@router.get("", response_model=list[TopicResponse])
async def list_topics(status: str = None, limit: int = 50):
    """List all topics, optionally filtered by status"""
    with get_db() as conn:
        cursor = conn.cursor()

        if status:
            cursor.execute(
                "SELECT * FROM topics WHERE status = ? LIMIT ?",
                (status, limit),
            )
        else:
            cursor.execute("SELECT * FROM topics LIMIT ?", (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str):
    """Get a specific topic"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Topic not found")

        return dict(row)


@router.post("/{topic_id}/approve")
async def approve_topic(topic_id: str):
    """Approve a topic"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE topics SET status = ?, approved_at = ?, updated_at = ? WHERE id = ?""",
            (
                "APPROVED",
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                topic_id,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Topic not found")

    return {"message": "Topic approved", "topic_id": topic_id}


@router.post("/{topic_id}/reject")
async def reject_topic(topic_id: str):
    """Reject a topic"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM topics WHERE id = ? AND status = ?",
            (topic_id, "DISCOVERED"),
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail="Topic cannot be rejected")

    return {"message": "Topic rejected", "topic_id": topic_id}
