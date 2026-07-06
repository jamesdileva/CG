"""Scripts API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import uuid
import logging
from backend.core.database import get_db
from backend.models.scripts import ScriptResponse, ScriptCreate, ScriptUpdate
from backend.llm import get_llm
from backend.llm.prompts import SCRIPT_GENERATION_PROMPT_TEMPLATE
from backend.llm.provider import GenerationParams
from backend.research.sources import get_research_bundle
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.video.scenes import save_scenes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scripts", tags=["scripts"])
orchestrator = PipelineOrchestrator()


async def generate_script_background(script_id: str, topic_id: str):
    """Background task to generate script"""
    try:
        # Get topic details
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, description FROM topics WHERE id = ?", (topic_id,))
            topic_row = cursor.fetchone()

            if not topic_row:
                logger.error(f"Topic {topic_id} not found")
                return

            topic_title = topic_row["title"]
            topic_description = topic_row["description"]

        research = get_research_bundle(topic_id)
        fact_lines = [
            f"- {fact['fact']}"
            for fact in research.get("facts", [])
        ]
        research_facts = "\n".join(fact_lines) if fact_lines else "- No saved research facts yet. Draft cautiously from topic description only."

        # Generate script
        llm = get_llm()
        prompt = SCRIPT_GENERATION_PROMPT_TEMPLATE.format(
            topic_title=topic_title,
            topic_description=topic_description,
            research_facts=research_facts,
        )
        params = GenerationParams(temperature=0.5, max_tokens=16384, num_ctx=16384)
        script_content = await llm.generate(prompt, params=params)

        # Save to database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE scripts SET content = ?, status = ?, updated_at = ? WHERE id = ?""",
                (
                    script_content,
                    "DRAFTED",
                    datetime.utcnow().isoformat(),
                    script_id,
                ),
            )
            conn.commit()

        await orchestrator.transition(topic_id, "SCRIPT_DRAFTED")
        logger.info(f"Generated script {script_id}")

        # Create scene records from the script so TTS has scene IDs to target
        try:
            save_scenes(script_id, topic_id, script_content)
        except Exception as e:
            logger.warning(f"Failed to save scenes during script generation: {e}")
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")


@router.post("/{topic_id}/generate")
async def generate_script(topic_id: str, background_tasks: BackgroundTasks = None):
    """Generate a script for a topic"""
    # Verify topic exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM topics WHERE id = ?", (topic_id,))
        topic = cursor.fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic["status"] not in {"APPROVED", "RESEARCH_COMPLETE", "SCRIPT_DRAFTED"}:
            raise HTTPException(
                status_code=400,
                detail="Topic must be approved or research-complete before script generation",
            )

    # Create script record
    script_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO scripts (id, topic_id, status, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                script_id,
                topic_id,
                "GENERATING",
                1,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

    # Generate in background
    if background_tasks:
        background_tasks.add_task(generate_script_background, script_id, topic_id)
    else:
        await generate_script_background(script_id, topic_id)

    return {"script_id": script_id, "status": "generating"}


@router.get("", response_model=list[ScriptResponse])
async def list_scripts():
    """List all scripts"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scripts ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/topic/{topic_id}", response_model=list[ScriptResponse])
async def get_topic_scripts(topic_id: str):
    """Get all scripts for a topic"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scripts WHERE topic_id = ? ORDER BY version DESC", (topic_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(script_id: str):
    """Get a specific script"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Script not found")

        return dict(row)


@router.post("/{script_id}/update")
async def update_script(script_id: str, update: ScriptUpdate):
    """Update script content"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE scripts SET content = ?, status = ?, version = version + 1, updated_at = ?
               WHERE id = ?""",
            (
                update.content,
                update.status or "DRAFTED",
                datetime.utcnow().isoformat(),
                script_id,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Script not found")

    return {"message": "Script updated", "script_id": script_id}


@router.post("/{script_id}/approve")
async def approve_script(script_id: str):
    """Approve a script"""
    topic_id = None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic_id FROM scripts WHERE id = ?", (script_id,))
        script = cursor.fetchone()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        topic_id = script["topic_id"]
        cursor.execute(
            """UPDATE scripts SET status = ?, approved_at = ?, updated_at = ? WHERE id = ?""",
            (
                "APPROVED",
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                script_id,
            ),
        )
        conn.commit()

    await orchestrator.transition(topic_id, "SCRIPT_APPROVED")

    return {"message": "Script approved", "script_id": script_id}
