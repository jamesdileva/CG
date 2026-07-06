from datetime import datetime
import logging
import shutil
import uuid

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from backend.core.config import settings
from backend.core.database import get_db
from backend.models.videos import VideoBundleResponse
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.video.renderer import (
    render_placeholder_video,
    render_scene_based_video,
    generate_thumbnail,
)
from backend.video.scenes import get_scenes_for_topic, save_scenes
from backend.video.tts import generate_all_scene_audio
from backend.research.image_extractor import extract_images_for_topic
from backend.assets.manager import store_asset, get_assets_for_topic, bulk_store_assets

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/videos", tags=["videos"])
orchestrator = PipelineOrchestrator()


def _latest_script_for_topic(topic_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM scripts
               WHERE topic_id = ? AND content IS NOT NULL
               ORDER BY CASE WHEN status = 'APPROVED' THEN 0 ELSE 1 END, updated_at DESC
               LIMIT 1""",
            (topic_id,),
        )
        return cursor.fetchone()


async def run_render_job(job_id: str, video_id: str, topic_id: str) -> None:
    try:
        await orchestrator.update_job(job_id, "RUNNING")
        script = _latest_script_for_topic(topic_id)
        if not script:
            raise ValueError("No script with content exists for this topic")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM topics WHERE id = ?", (topic_id,))
            topic = cursor.fetchone()
            if not topic:
                raise ValueError("Topic not found")

        scenes = get_scenes_for_topic(topic_id)
        if not scenes:
            scenes = save_scenes(script["id"], topic_id, script["content"])

        # Clean stale image assets and files from previous runs
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM assets WHERE topic_id = ? AND type = 'image'", (topic_id,)
            )
            conn.commit()
        images_dir = Path(__file__).parent.parent.parent / "data" / "projects" / topic_id / "images"
        if images_dir.exists():
            shutil.rmtree(str(images_dir))

        # Extract images before loading assets so they're available for render
        try:
            downloaded = await extract_images_for_topic(topic_id)
            if downloaded and scenes:
                asset_records = []
                for i, img in enumerate(downloaded):
                    scene_id = scenes[i % len(scenes)]["id"]
                    asset_records.append({
                        "type": "image",
                        "file_path": img["file_path"],
                        "topic_id": topic_id,
                        "source_url": img["source_url"],
                        "scene_id": scene_id,
                        "caption": img.get("caption", ""),
                    })
                bulk_store_assets(asset_records)
                logger.info("Stored %d images for topic %s", len(asset_records), topic_id)
        except Exception:
            logger.exception("Image extraction failed, continuing without images")

        assets = get_assets_for_topic(topic_id)
        audio_assets = [a for a in assets if a["type"] == "audio"]
        image_assets = [a for a in assets if a["type"] == "image"]

        scene_audio_map = {}
        for audio in audio_assets:
            if audio["scene_id"]:
                scene_audio_map[audio["scene_id"]] = audio["file_path"]

        scene_image_map = {}
        scene_caption_map = {}
        if image_assets:
            num_scenes = len(scenes)
            for idx, scene in enumerate(scenes):
                img_idx = idx * len(image_assets) // num_scenes
                img_idx = min(img_idx, len(image_assets) - 1)
                img = image_assets[img_idx]
                scene_image_map[scene["id"]] = img["file_path"]
                scene_caption_map[scene["id"]] = img.get("caption", "")

        use_background_music = True

        if scene_audio_map:
            render_result = render_scene_based_video(
                topic_id, topic["title"], scenes, scene_audio_map, scene_image_map,
                scene_caption_map=scene_caption_map,
                background_music=use_background_music,
            )
        else:
            render_result = render_placeholder_video(topic_id, topic["title"], scenes)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE videos
                   SET script_id = ?, status = ?, file_path = ?, duration_seconds = ?,
                       file_size_bytes = ?, completed_at = ?
                   WHERE id = ?""",
                (
                    script["id"],
                    "RENDERED",
                    render_result["file_path"],
                    render_result["duration_seconds"],
                    render_result["file_size_bytes"],
                    datetime.utcnow().isoformat(),
                    video_id,
                ),
            )
            conn.commit()

        await orchestrator.transition(topic_id, "VIDEO_RENDERED")
        await orchestrator.update_job(job_id, "COMPLETE", result=render_result)
    except Exception as exc:
        logger.exception("Video render failed")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE videos SET status = ? WHERE id = ?", ("FAILED", video_id))
            conn.commit()
        await orchestrator.update_job(job_id, "FAILED", error=str(exc))


@router.post("/render/{topic_id}")
async def render_video(topic_id: str, background_tasks: BackgroundTasks, background_music: bool = True):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM topics WHERE id = ?", (topic_id,))
        topic = cursor.fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic["status"] not in {"SCRIPT_DRAFTED", "SCRIPT_APPROVED", "VIDEO_RENDERED"}:
            raise HTTPException(status_code=400, detail="Generate a script before rendering video")

    video_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO videos (id, topic_id, status, created_at)
               VALUES (?, ?, ?, ?)""",
            (video_id, topic_id, "RENDERING", now),
        )
        conn.commit()

    job_id = await orchestrator.create_job("video_render", topic_id, {"video_id": video_id, "background_music": background_music})
    background_tasks.add_task(run_render_job, job_id, video_id, topic_id)
    return {"message": "Video render started", "topic_id": topic_id, "video_id": video_id, "job_id": job_id}


@router.post("/tts/{topic_id}")
async def generate_tts(topic_id: str, background_tasks: BackgroundTasks, rate: str = "+0%", voice: str = ""):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

    scenes = get_scenes_for_topic(topic_id)
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes found. Render the video first to generate scenes.")

    effective_voice = voice.strip() or settings.tts_voice

    async def run_tts():
        results = await generate_all_scene_audio(scenes, topic_id, rate=rate, voice=effective_voice)
        asset_records = []
        for r in results:
            asset_records.append({
                "type": "audio",
                "file_path": r["audio_path"],
                "topic_id": topic_id,
                "scene_id": r["scene_id"],
            })
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE scenes SET audio_path = ? WHERE id = ?",
                    (r["audio_path"], r["scene_id"]),
                )
                conn.commit()
        bulk_store_assets(asset_records)

    background_tasks.add_task(run_tts)
    return {"message": "TTS generation started", "topic_id": topic_id, "scenes_count": len(scenes)}


@router.get("/tts/{topic_id}")
async def get_tts_status(topic_id: str):
    scenes = get_scenes_for_topic(topic_id)
    return {
        "topic_id": topic_id,
        "scenes": [
            {
                "id": s["id"],
                "order_index": s["order_index"],
                "has_audio": bool(s.get("audio_path")),
                "audio_path": s.get("audio_path"),
            }
            for s in scenes
        ],
    }


@router.post("/images/{topic_id}")
async def extract_images(topic_id: str, background_tasks: BackgroundTasks):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

    from backend.assets.manager import get_assets_for_topic
    existing = get_assets_for_topic(topic_id, asset_type="image")
    if existing:
        return {"message": "Images already exist, skipping extraction", "topic_id": topic_id, "count": len(existing)}

    async def run_extract():
        images = await extract_images_for_topic(topic_id)
        scenes = get_scenes_for_topic(topic_id)
        asset_records = []
        for i, img in enumerate(images):
            scene_id = scenes[i % len(scenes)]["id"] if scenes else None
            asset_records.append({
                "type": "image",
                "file_path": img["file_path"],
                "topic_id": topic_id,
                "source_url": img["source_url"],
                "scene_id": scene_id,
            })
        bulk_store_assets(asset_records)

    background_tasks.add_task(run_extract)
    return {"message": "Image extraction started", "topic_id": topic_id}


@router.get("/assets/{topic_id}")
async def list_assets(topic_id: str, asset_type: str | None = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

    assets = get_assets_for_topic(topic_id, asset_type)
    return {"topic_id": topic_id, "assets": assets}


@router.post("/thumbnail/{topic_id}")
async def create_thumbnail(topic_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE topic_id = ? AND status = 'RENDERED' ORDER BY created_at DESC LIMIT 1",
            (topic_id,),
        )
        video = cursor.fetchone()
        if not video:
            raise HTTPException(status_code=400, detail="No rendered video found for this topic")

    thumbnail_path = generate_thumbnail(video["file_path"])
    asset = store_asset("thumbnail", thumbnail_path, topic_id)
    return {"message": "Thumbnail generated", "asset": asset}


@router.get("/{topic_id}", response_model=VideoBundleResponse)
async def get_video(topic_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")
        cursor.execute(
            "SELECT * FROM videos WHERE topic_id = ? ORDER BY created_at DESC LIMIT 1",
            (topic_id,),
        )
        video = cursor.fetchone()

    return {
        "topic_id": topic_id,
        "video": dict(video) if video else None,
        "scenes": get_scenes_for_topic(topic_id),
    }


@router.get("/asset-file/{topic_id}/{filename:path}")
async def get_asset_file(topic_id: str, filename: str):
    """Serve an asset file (image/audio/thumbnail) by topic and filename."""
    from backend.video.scenes import PROJECTS_DIR
    safe_name = Path(filename).name
    file_path = PROJECTS_DIR / topic_id / "images" / safe_name
    if not file_path.exists():
        file_path = PROJECTS_DIR / topic_id / "video" / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Asset file not found")
    return FileResponse(str(file_path))
