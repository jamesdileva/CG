"""Topics API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
import logging

from backend.core.database import get_db
from backend.models.topics import TopicCreate, TopicResponse, TopicUpdate
from backend.llm import get_llm
from backend.llm.prompts import TOPIC_GENERATION_PROMPT, WEIRD_HISTORY_PROMPT, TRUE_CRIME_PROMPT, MYSTERY_PROMPT
from backend.llm.provider import GenerationParams
from backend.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/topics", tags=["topics"])
orchestrator = PipelineOrchestrator()


class TopicSchema(BaseModel):
    title: str
    description: str


class TopicListSchema(BaseModel):
    topics: list[TopicSchema]


class GenerateTopicsRequest(BaseModel):
    num_topics: int = Field(default=5, ge=1, le=20)
    style: str = Field(default="default", pattern=r"^(default|weird_history|true_crime|mystery)$")


_PROMPT_MAP = {
    "default": TOPIC_GENERATION_PROMPT,
    "weird_history": WEIRD_HISTORY_PROMPT,
    "true_crime": TRUE_CRIME_PROMPT,
    "mystery": MYSTERY_PROMPT,
}


async def generate_topics_background(num_topics: int = 5, style: str = "default"):
    """Background task to generate topics using LLM"""
    try:
        llm = get_llm()
        template = _PROMPT_MAP.get(style, TOPIC_GENERATION_PROMPT)
        prompt = template.format(num_topics=num_topics)

        # Fetch existing topics to avoid regenerating duplicates
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM topics ORDER BY created_at DESC LIMIT 50")
            existing = [row["title"] for row in cursor.fetchall() if row["title"]]
        if existing:
            exclude_list = "\n".join(f"- {t}" for t in existing)
            prompt += (
                f"\n\nCRITICAL — DO NOT REPEAT: The following topics have ALREADY BEEN GENERATED."
                f" You MUST NOT generate any of these or similar topics:\n{exclude_list}"
                f"\n\nGenerate completely new, different topics not on this list."
            )

        params = GenerationParams(
            temperature=0.85,
            max_tokens=2048,
            seed=int(datetime.utcnow().timestamp()),
            frequency_penalty=0.3,
            presence_penalty=0.3,
        )
        data = await llm.generate_structured(prompt, params=params)

        topics_data = data.get("topics", []) if isinstance(data, dict) else data
        if not isinstance(topics_data, list):
            topics_data = [topics_data]

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
async def generate_topics(
    request: Optional[GenerateTopicsRequest] = None,
    background_tasks: BackgroundTasks = None,
    num_topics: Optional[int] = None,
    style: Optional[str] = None,
):
    """Generate new documentary topics"""
    if request:
        count = request.num_topics
        gen_style = request.style
    else:
        count = num_topics or 5
        gen_style = style or "default"

    if background_tasks:
        background_tasks.add_task(generate_topics_background, count, gen_style)
        return {"message": f"Topic generation started ({gen_style})", "status": "processing"}
    else:
        await generate_topics_background(count, gen_style)
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


@router.delete("/{topic_id}")
async def delete_topic(topic_id: str):
    """Delete a topic and all related data."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

        cursor.execute("DELETE FROM research_facts WHERE topic_id = ?", (topic_id,))
        cursor.execute("DELETE FROM research_sources WHERE topic_id = ?", (topic_id,))
        cursor.execute("DELETE FROM assets WHERE topic_id = ?", (topic_id,))
        cursor.execute("DELETE FROM scenes WHERE script_id IN (SELECT id FROM scripts WHERE topic_id = ?)", (topic_id,))
        cursor.execute("DELETE FROM scripts WHERE topic_id = ?", (topic_id,))
        cursor.execute("SELECT id FROM videos WHERE topic_id = ?", (topic_id,))
        video_ids = [row["id"] for row in cursor.fetchall()]
        for vid in video_ids:
            cursor.execute("DELETE FROM analytics WHERE video_id = ?", (vid,))
            cursor.execute("DELETE FROM youtube_uploads WHERE video_id = ?", (vid,))
        cursor.execute("DELETE FROM videos WHERE topic_id = ?", (topic_id,))
        cursor.execute("DELETE FROM jobs WHERE topic_id = ?", (topic_id,))
        cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        conn.commit()

    return {"message": "Topic deleted", "topic_id": topic_id}
