from __future__ import annotations

import logging
from datetime import datetime
import uuid

from googleapiclient.discovery import build

from backend.core.database import get_db
from backend.youtube.auth import load_credentials, is_authenticated

logger = logging.getLogger(__name__)


def _score_metrics(views: int, likes: int, comments: int, watch_time: int, ctr: float) -> float:
    engagement = (likes * 3 + comments * 5) / max(views, 1)
    retention = watch_time / max(views * 600, 1)
    score = min(100.0, views / 100.0 + engagement * 100.0 + retention * 40.0 + ctr * 8.0)
    return round(score, 2)


def pull_youtube_analytics() -> list[dict]:
    if not is_authenticated():
        raise RuntimeError("YouTube authentication required")

    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT yu.youtube_id, yu.video_id, yu.id as upload_id, v.topic_id "
            "FROM youtube_uploads yu "
            "JOIN videos v ON v.id = yu.video_id "
            "WHERE yu.youtube_id IS NOT NULL "
            "AND yu.youtube_id NOT LIKE 'local-%' "
            "AND yu.status = 'UPLOADED'"
        )
        rows = cursor.fetchall()

    ingested = []
    now = datetime.utcnow().isoformat()

    for row in rows:
        youtube_id = row["youtube_id"]
        if not youtube_id:
            continue

        try:
            request = youtube.videos().list(
                part="statistics",
                id=youtube_id,
            )
            response = request.execute()

            items = response.get("items", [])
            if not items:
                logger.warning("No stats found for video %s", youtube_id)
                continue

            stats = items[0].get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))

            topic_score = _score_metrics(views, likes, comments, 0, 0.0)

            with get_db() as conn:
                cursor = conn.cursor()
                analytics_id = str(uuid.uuid4())
                cursor.execute(
                    """INSERT INTO analytics
                       (id, video_id, youtube_id, views, likes, comments,
                        watch_time_seconds, click_through_rate, topic_score, synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (analytics_id, row["video_id"], youtube_id, views, likes, comments,
                     0, 0.0, topic_score, now),
                )
                conn.commit()

            ingested.append({
                "youtube_id": youtube_id,
                "views": views,
                "likes": likes,
                "comments": comments,
                "topic_score": topic_score,
            })
            logger.info("Pulled analytics for %s: %d views, score %.2f", youtube_id, views, topic_score)

        except Exception as exc:
            logger.exception("Failed to pull analytics for %s: %s", youtube_id, exc)

    return ingested
