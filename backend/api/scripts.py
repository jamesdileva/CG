"""Scripts API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import uuid
import logging
from backend.core.database import get_db
from backend.models.scripts import ScriptResponse, ScriptCreate, ScriptUpdate
from backend.llm import get_llm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scripts", tags=["scripts"])

# Script generation prompt template
SCRIPT_GENERATION_PROMPT_TEMPLATE = """Generate a compelling documentary script for the following topic:

Topic: {topic_title}
Description: {topic_description}

The script should:
- Be suitable for a 10-15 minute documentary
- Have 3-4 main sections with clear transitions
- Include specific facts and dates where relevant
- Be written for a general audience
- Include [VISUAL] markers for where images/b-roll should appear

Start with a compelling hook that engages the viewer immediately."""


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

        # Generate script
        llm = get_llm()
        prompt = SCRIPT_GENERATION_PROMPT_TEMPLATE.format(
            topic_title=topic_title,
            topic_description=topic_description,
        )
        script_content = await llm.generate(prompt)

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

        logger.info(f"Generated script {script_id}")
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")


@router.post("/{topic_id}/generate")
async def generate_script(topic_id: str, background_tasks: BackgroundTasks = None):
    """Generate a script for a topic"""
    # Verify topic exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

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


@router.get("/topic/{topic_id}", response_model=list[ScriptResponse])
async def get_topic_scripts(topic_id: str):
    """Get all scripts for a topic"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scripts WHERE topic_id = ? ORDER BY version DESC", (topic_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


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
    with get_db() as conn:
        cursor = conn.cursor()
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

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Script not found")

    return {"message": "Script approved", "script_id": script_id}
