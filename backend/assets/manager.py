from __future__ import annotations

from datetime import datetime
from pathlib import Path
import uuid

from backend.core.database import get_db


def store_asset(
    asset_type: str,
    file_path: str,
    topic_id: str,
    scene_id: str | None = None,
    source_url: str | None = None,
    caption: str | None = None,
) -> dict:
    asset_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO assets (id, type, file_path, topic_id, scene_id, source_url, caption, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (asset_id, asset_type, file_path, topic_id, scene_id, source_url, caption, now),
        )
        conn.commit()

    return {
        "id": asset_id,
        "type": asset_type,
        "file_path": file_path,
        "topic_id": topic_id,
        "scene_id": scene_id,
        "source_url": source_url,
        "caption": caption,
        "created_at": now,
    }


def get_assets_for_topic(topic_id: str, asset_type: str | None = None) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        if asset_type:
            cursor.execute(
                "SELECT * FROM assets WHERE topic_id = ? AND type = ? ORDER BY created_at DESC",
                (topic_id, asset_type),
            )
        else:
            cursor.execute(
                "SELECT * FROM assets WHERE topic_id = ? ORDER BY type, created_at DESC",
                (topic_id,),
            )
        return [dict(row) for row in cursor.fetchall()]


def get_assets_for_scene(scene_id: str) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM assets WHERE scene_id = ? ORDER BY type, created_at DESC",
            (scene_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_asset(asset_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM assets WHERE id = ?", (asset_id,))
        row = cursor.fetchone()
        if not row:
            return False

        file_path = Path(row["file_path"])
        if file_path.exists():
            file_path.unlink()

        cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()

    return True


def bulk_store_assets(assets: list[dict]) -> list[dict]:
    stored = []
    for asset in assets:
        stored.append(
            store_asset(
                asset_type=asset["type"],
                file_path=asset["file_path"],
                topic_id=asset["topic_id"],
                scene_id=asset.get("scene_id"),
                source_url=asset.get("source_url"),
                caption=asset.get("caption"),
            )
        )
    return stored
