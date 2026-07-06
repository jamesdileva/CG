from datetime import datetime
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.core.database import get_db
from backend.models.analytics import AnalyticsIngestRequest, AnalyticsSummaryResponse
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.analytics.puller import pull_youtube_analytics
from backend.analytics.ranker import (
    rank_topics,
    get_low_performers,
    get_dashboard_summary,
    update_topic_scores,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])
orchestrator = PipelineOrchestrator()


def _score_metrics(views: int, likes: int, comments: int, watch_time: int, ctr: float) -> float:
    engagement = (likes * 3 + comments * 5) / max(views, 1)
    retention = watch_time / max(views * 600, 1)
    score = min(100.0, views / 100.0 + engagement * 100.0 + retention * 40.0 + ctr * 8.0)
    return round(score, 2)


@router.post("/ingest")
async def ingest_analytics(request: AnalyticsIngestRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic_id FROM videos WHERE id = ?", (request.video_id,))
        video = cursor.fetchone()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        analytics_id = str(uuid.uuid4())
        topic_score = _score_metrics(
            request.views,
            request.likes,
            request.comments,
            request.watch_time_seconds,
            request.click_through_rate,
        )
        cursor.execute(
            """INSERT INTO analytics
               (id, video_id, youtube_id, views, likes, comments, watch_time_seconds,
                click_through_rate, topic_score, synced_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analytics_id,
                request.video_id,
                request.youtube_id,
                request.views,
                request.likes,
                request.comments,
                request.watch_time_seconds,
                request.click_through_rate,
                topic_score,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

    await orchestrator.transition(video["topic_id"], "ANALYTICS_COLLECTED")
    update_topic_scores()

    return {"message": "Analytics ingested", "analytics_id": analytics_id, "topic_score": topic_score}


@router.post("/pull")
async def pull_analytics(background_tasks: BackgroundTasks):
    async def run_pull():
        try:
            results = pull_youtube_analytics()
            update_topic_scores()
            logger.info("Auto-pulled analytics for %d videos", len(results))
        except RuntimeError as exc:
            logger.warning("Analytics pull skipped: %s", exc)

    background_tasks.add_task(run_pull)
    return {"message": "YouTube analytics pull started"}


@router.get("/rankings")
async def get_rankings(limit: int = 10):
    try:
        top = rank_topics(limit)
        low = get_low_performers(limit=limit)
        summary = get_dashboard_summary()
    except Exception as exc:
        logger.exception("Failed to compute rankings")
        return {
            "summary": {"total_topics": 0, "average_interest_score": 0.0, "top_topic": None, "total_analytics_ingests": 0, "total_views": 0},
            "top_performers": [],
            "low_performers": [],
            "error": str(exc),
        }
    return {
        "summary": summary,
        "top_performers": top,
        "low_performers": low,
    }


@router.get("/{video_id}", response_model=AnalyticsSummaryResponse)
async def get_analytics(video_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM videos WHERE id = ?", (video_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Video not found")
        cursor.execute(
            "SELECT * FROM analytics WHERE video_id = ? ORDER BY synced_at DESC",
            (video_id,),
        )
        history = [dict(row) for row in cursor.fetchall()]

    return {"video_id": video_id, "latest": history[0] if history else None, "history": history}


@router.get("")
async def list_analytics():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT analytics.*, topics.title as topic_title, topics.interest_score, videos.file_path
                   FROM analytics
                   JOIN videos ON videos.id = analytics.video_id
                   JOIN topics ON topics.id = videos.topic_id
                   ORDER BY analytics.synced_at DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.exception("Failed to list analytics")
        return []
