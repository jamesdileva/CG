from __future__ import annotations

import logging
from datetime import datetime

from backend.core.database import get_db

logger = logging.getLogger(__name__)

_TOPIC_SCORE_DECAY = 0.7


def update_topic_scores() -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT topics.id,
                      COALESCE(AVG(analytics.topic_score), 0.0) as avg_score,
                      COALESCE(MAX(analytics.views), 0) as max_views,
                      COUNT(analytics.id) as ingest_count
               FROM topics
               LEFT JOIN videos ON videos.topic_id = topics.id
               LEFT JOIN analytics ON analytics.video_id = videos.id
               WHERE topics.status IN ('UPLOADED', 'ANALYTICS_COLLECTED', 'ARCHIVED')
               GROUP BY topics.id
               ORDER BY avg_score DESC"""
        )
        rows = cursor.fetchall()

    now = datetime.utcnow().isoformat()
    updated = 0

    with get_db() as conn:
        cursor = conn.cursor()
        for row in rows:
            avg_score = row["avg_score"]
            max_views = row["max_views"]
            ingest_count = row["ingest_count"]

            views_factor = min(max_views / 1000.0, 10.0)
            confidence = min(ingest_count / 3.0, 1.0)
            blended = avg_score * _TOPIC_SCORE_DECAY + views_factor * (1 - _TOPIC_SCORE_DECAY)
            final_score = round(blended * confidence, 2)

            cursor.execute(
                "UPDATE topics SET interest_score = ?, updated_at = ? WHERE id = ?",
                (final_score, now, row["id"]),
            )
            updated += 1

        conn.commit()

    logger.info("Updated interest scores for %d topics", updated)
    return updated


def rank_topics(limit: int = 10) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, title, status, interest_score, uniqueness_score, source_score, category
               FROM topics
               WHERE interest_score > 0
               ORDER BY interest_score DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_low_performers(threshold: float = 10.0, limit: int = 10) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, title, status, interest_score
               FROM topics
               WHERE interest_score > 0 AND interest_score < ?
               ORDER BY interest_score ASC
               LIMIT ?""",
            (threshold, limit),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_dashboard_summary() -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM topics")
        total_topics = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COALESCE(AVG(interest_score), 0.0) as avg FROM topics WHERE interest_score > 0"
        )
        avg_score = cursor.fetchone()["avg"]

        cursor.execute(
            "SELECT id, title, interest_score FROM topics WHERE interest_score > 0 ORDER BY interest_score DESC LIMIT 1"
        )
        top = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as count FROM analytics")
        total_ingests = cursor.fetchone()["count"]

        cursor.execute("SELECT COALESCE(SUM(views), 0) as total FROM analytics")
        total_views = cursor.fetchone()["total"]

    return {
        "total_topics": total_topics,
        "average_interest_score": round(avg_score, 2),
        "top_topic": dict(top) if top else None,
        "total_analytics_ingests": total_ingests,
        "total_views": total_views,
    }
