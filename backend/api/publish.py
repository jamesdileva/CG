from datetime import datetime
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models.publish import MetadataBuildRequest, UploadResponse, UploadUpdateRequest
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.youtube.auth import is_authenticated, get_auth_url, exchange_code
from backend.youtube.uploader import upload_video

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/publish", tags=["publish"])
orchestrator = PipelineOrchestrator()


class AuthCodeRequest(BaseModel):
    code: str


def _build_default_metadata(video_id: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT videos.id as video_id, videos.file_path, topics.id as topic_id,
                      topics.title, topics.description
               FROM videos
               JOIN topics ON topics.id = videos.topic_id
               WHERE videos.id = ?""",
            (video_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Video not found")

    title = row["title"][:90]
    description = f"{row['description'] or row['title']}"
    tags = ["documentary", "history", "education", "longform"]
    return {"title": title, "description": description, "tags": tags}


def _latest_rendered_video(topic_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE topic_id = ? AND status = 'RENDERED' ORDER BY created_at DESC LIMIT 1",
            (topic_id,),
        )
        return cursor.fetchone()


@router.post("/metadata", response_model=UploadResponse)
async def build_metadata(request: MetadataBuildRequest):
    try:
        defaults = _build_default_metadata(request.video_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    title = request.title or defaults["title"]
    description = request.description or defaults["description"]
    tags = request.tags or defaults["tags"]
    upload_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM videos WHERE id = ? AND status = ?",
            (request.video_id, "RENDERED"),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Video must be rendered before metadata can be built")
        cursor.execute(
            """INSERT INTO youtube_uploads
               (id, video_id, title, description, tags, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (upload_id, request.video_id, title, description, json.dumps(tags), "METADATA_READY", now),
        )
        conn.commit()
        cursor.execute("SELECT * FROM youtube_uploads WHERE id = ?", (upload_id,))
        return dict(cursor.fetchone())


@router.get("", response_model=list[UploadResponse])
async def list_uploads(status: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "SELECT * FROM youtube_uploads WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            cursor.execute("SELECT * FROM youtube_uploads ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(upload_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM youtube_uploads WHERE id = ?", (upload_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Upload record not found")
        return dict(row)


@router.post("/{upload_id}/update", response_model=UploadResponse)
async def update_upload(upload_id: str, request: UploadUpdateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM youtube_uploads WHERE id = ?", (upload_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Upload record not found")

        title = request.title if request.title is not None else existing["title"]
        description = request.description if request.description is not None else existing["description"]
        tags = json.dumps(request.tags) if request.tags is not None else existing["tags"]
        scheduled_at = request.scheduled_at.isoformat() if request.scheduled_at else existing["scheduled_at"]
        cursor.execute(
            """UPDATE youtube_uploads
               SET title = ?, description = ?, tags = ?, scheduled_at = ?, status = ?
               WHERE id = ?""",
            (title, description, tags, scheduled_at, "METADATA_READY", upload_id),
        )
        conn.commit()
        cursor.execute("SELECT * FROM youtube_uploads WHERE id = ?", (upload_id,))
        return dict(cursor.fetchone())


@router.post("/{upload_id}/approve")
async def approve_upload(upload_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE youtube_uploads SET status = ? WHERE id = ?",
            ("READY_TO_UPLOAD", upload_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Upload record not found")
        cursor.execute(
            """SELECT videos.topic_id
               FROM youtube_uploads
               JOIN videos ON videos.id = youtube_uploads.video_id
               WHERE youtube_uploads.id = ?""",
            (upload_id,),
        )
        row = cursor.fetchone()

    if row:
        await orchestrator.transition(row["topic_id"], "READY_TO_UPLOAD")
    return {"message": "Upload approved", "upload_id": upload_id}


@router.get("/auth/status")
async def auth_status():
    return {"authenticated": is_authenticated()}


@router.get("/auth/url")
async def auth_url():
    url = get_auth_url()
    return {"auth_url": url}


@router.post("/auth/callback")
async def auth_callback(request: AuthCodeRequest):
    try:
        exchange_code(request.code)
        return {"message": "Authentication successful"}
    except Exception as exc:
        logger.exception("OAuth callback failed")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {exc}")


async def _run_youtube_upload(job_id: str, upload_id: str) -> None:
    await orchestrator.update_job(job_id, "RUNNING")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT youtube_uploads.*, videos.file_path, videos.topic_id
                   FROM youtube_uploads
                   JOIN videos ON videos.id = youtube_uploads.video_id
                   WHERE youtube_uploads.id = ?""",
                (upload_id,),
            )
            row = cursor.fetchone()

        if not row or not row["file_path"]:
            raise RuntimeError("Upload record or video file not found")

        from backend.assets.manager import get_assets_for_topic
        assets = get_assets_for_topic(row["topic_id"], "thumbnail")
        thumbnail_path = assets[0]["file_path"] if assets else None

        tags_list = json.loads(row["tags"]) if row["tags"] else []
        result = upload_video(
            video_path=row["file_path"],
            title=row["title"] or row["id"],
            description=row["description"] or "",
            tags=tags_list,
            thumbnail_path=thumbnail_path,
        )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE youtube_uploads
                   SET status = ?, youtube_id = ?, uploaded_at = ?
                   WHERE id = ?""",
                ("UPLOADED", result["youtube_id"], datetime.utcnow().isoformat(), upload_id),
            )
            conn.commit()

        await orchestrator.transition(row["topic_id"], "UPLOADED")
        await orchestrator.update_job(job_id, "COMPLETE", result=result)
    except Exception as exc:
        logger.exception("YouTube upload failed")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE youtube_uploads SET status = ? WHERE id = ?",
                ("UPLOAD_FAILED", upload_id),
            )
            conn.commit()
        await orchestrator.update_job(job_id, "FAILED", error=str(exc))


@router.post("/{upload_id}/upload-to-youtube")
async def upload_to_youtube(upload_id: str, background_tasks: BackgroundTasks):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM youtube_uploads WHERE id = ?",
            (upload_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Upload record not found")
        if row["status"] != "READY_TO_UPLOAD":
            raise HTTPException(status_code=400, detail="Upload must be approved first")

    job_id = await orchestrator.create_job("youtube_upload", upload_id, {"upload_id": upload_id})
    background_tasks.add_task(_run_youtube_upload, job_id, upload_id)
    return {
        "message": "YouTube upload started",
        "upload_id": upload_id,
        "job_id": job_id,
    }


@router.post("/{upload_id}/mock-upload")
async def mock_upload(upload_id: str):
    youtube_id = f"local-{upload_id[:8]}"
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE youtube_uploads
               SET status = ?, youtube_id = ?, uploaded_at = ?
               WHERE id = ? AND status IN ('READY_TO_UPLOAD', 'METADATA_READY')""",
            ("UPLOADED", youtube_id, now, upload_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail="Upload must exist and be ready")
        cursor.execute(
            """SELECT videos.topic_id
               FROM youtube_uploads
               JOIN videos ON videos.id = youtube_uploads.video_id
               WHERE youtube_uploads.id = ?""",
            (upload_id,),
        )
        row = cursor.fetchone()

    if row:
        await orchestrator.transition(row["topic_id"], "UPLOADED")
    return {"message": "Mock upload complete", "upload_id": upload_id, "youtube_id": youtube_id}
