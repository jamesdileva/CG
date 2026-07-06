"""Scene splitting and persistence helpers."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import uuid

from backend.core.database import get_db


PROJECTS_DIR = Path(__file__).parent.parent.parent / "data" / "projects"


def _strip_directives(text: str) -> str:
    """Remove ALL [bracket] directives and (stage direction) markers from scene text.
    
    This catches standard markers ([NARRATOR:], [VISUAL:], [SECTION:]) plus any
    LLM-invented placeholders like [archival photo goes here], [insert image], etc.
    """
    text = re.sub(r"\[[^\]]*\]\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\([^)]*(?:image|photo|picture|footage|video|show|display|insert|here)[^)]*\)\s*", "", text, flags=re.IGNORECASE).strip()
    return text


def split_script_into_scenes(script_content: str, max_scenes: int = 40) -> list[dict]:
    """Split a script into scenes.

    If the script uses [SECTION:] markers, group all paragraphs within each
    section into a single scene. Otherwise fall back to splitting on double
    newlines and [VISUAL:] markers (per-paragraph behaviour).
    """
    text = (script_content or "")
    if not text.strip():
        return []

    has_sections = bool(re.search(r"\[SECTION[^\]]*\]", text))

    if has_sections:
        # Split on [SECTION:] boundaries — each block becomes one scene
        section_blocks = re.split(r"(?=\[SECTION[^\]]*\])", text)
        scenes = []
        order = 0
        for block in section_blocks:
            block = block.strip()
            if not block:
                continue
            scene_text = _strip_directives(block)
            scene_text = scene_text.replace("*", "").strip()
            scene_text = " ".join(scene_text.split())
            if not scene_text or len(scene_text.split()) < 3:
                continue
            if len(scenes) >= max_scenes:
                break
            duration = max(30.0, len(scene_text.split()) / 2.0)
            scenes.append({"order_index": order, "text": scene_text, "duration": round(duration, 2)})
            order += 1
    else:
        # Old behaviour: split on double newlines and [VISUAL:] markers
        chunks = [chunk.strip() for chunk in re.split(
            r"\n\s*\n|\[VISUAL[^\]]*\]",
            text,
        ) if chunk.strip()]
        if not chunks:
            chunks = [script_content.strip() or "Documentary scene"]

        scenes = []
        for index, chunk in enumerate(chunks[:max_scenes]):
            scene_text = _strip_directives(chunk)
            scene_text = scene_text.replace("*", "").strip()
            scene_text = " ".join(scene_text.split())
            if not scene_text or len(scene_text.split()) < 3:
                continue
            duration = max(30.0, len(scene_text.split()) / 2.0)
            scenes.append({"order_index": index, "text": scene_text, "duration": round(duration, 2)})

    if not scenes and script_content:
        scenes.append({"order_index": 0, "text": "Documentary scene", "duration": 30.0})

    return scenes


def save_scenes(script_id: str, topic_id: str, script_content: str) -> list[dict]:
    """Create scene rows and write a scene manifest for a topic."""
    scenes = split_script_into_scenes(script_content)
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM scenes WHERE id IN (SELECT s.id FROM scenes s JOIN scripts sc ON sc.id = s.script_id WHERE sc.topic_id = ?)",
            (topic_id,),
        )
        saved = []
        for scene in scenes:
            scene_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO scenes
                   (id, script_id, order_index, text, duration, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (scene_id, script_id, scene["order_index"], scene["text"], scene["duration"], now),
            )
            saved.append(
                {
                    "id": scene_id,
                    "script_id": script_id,
                    "order_index": scene["order_index"],
                    "text": scene["text"],
                    "image_path": None,
                    "audio_path": None,
                    "duration": scene["duration"],
                    "created_at": now,
                }
            )
        conn.commit()

    project_dir = PROJECTS_DIR / topic_id
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "scenes.json").write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return saved


def get_scenes_for_topic(topic_id: str) -> list[dict]:
    """Load scenes for the latest script of a topic."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT scenes.*
               FROM scenes
               JOIN scripts ON scripts.id = scenes.script_id
               WHERE scripts.topic_id = ?
                 AND scripts.id = (
                   SELECT id FROM scripts
                   WHERE topic_id = ? AND content IS NOT NULL
                   ORDER BY updated_at DESC LIMIT 1
                 )
               ORDER BY scenes.order_index ASC""",
            (topic_id, topic_id),
        )
        return [dict(row) for row in cursor.fetchall()]
