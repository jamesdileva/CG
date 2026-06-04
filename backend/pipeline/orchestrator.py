"""Pipeline orchestrator - manages topic state transitions"""
from typing import Optional
import logging
from datetime import datetime
import json
from backend.core.database import get_db

logger = logging.getLogger(__name__)

# State machine definition
VALID_TRANSITIONS = {
    "DISCOVERED": ["APPROVED"],
    "APPROVED": ["RESEARCHING"],
    "RESEARCHING": ["RESEARCH_COMPLETE"],
    "RESEARCH_COMPLETE": ["SCRIPT_DRAFTED"],
    "SCRIPT_DRAFTED": ["SCRIPT_APPROVED"],
    "SCRIPT_APPROVED": ["VIDEO_RENDERED"],
}


class PipelineOrchestrator:
    """Manages pipeline state machine and transitions"""

    async def can_transition(self, topic_id: str, new_status: str) -> bool:
        """Check if transition is valid"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM topics WHERE id = ?", (topic_id,))
            row = cursor.fetchone()

            if not row:
                return False

            current_status = row["status"]
            valid_next_states = VALID_TRANSITIONS.get(current_status, [])
            return new_status in valid_next_states

    async def transition(self, topic_id: str, new_status: str) -> bool:
        """Transition topic to new status"""
        if not await self.can_transition(topic_id, new_status):
            logger.warning(f"Invalid transition for {topic_id} to {new_status}")
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE topics SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, datetime.utcnow().isoformat(), topic_id),
            )
            conn.commit()

        logger.info(f"Topic {topic_id} transitioned to {new_status}")
        return True

    async def create_job(
        self, job_type: str, topic_id: Optional[str] = None, payload: Optional[dict] = None
    ) -> str:
        """Create async job"""
        import uuid

        job_id = str(uuid.uuid4())
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO jobs (id, type, topic_id, status, payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    job_id,
                    job_type,
                    topic_id,
                    "PENDING",
                    json.dumps(payload) if payload else None,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id

    async def update_job(
        self,
        job_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ):
        """Update job status"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE jobs SET status = ?, result = ?, error = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    status,
                    json.dumps(result) if result else None,
                    error,
                    datetime.utcnow().isoformat(),
                    job_id,
                ),
            )
            conn.commit()

        logger.info(f"Job {job_id} updated to {status}")

    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get job status and result"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()

            if not row:
                return None

            result = dict(row)
            if result.get("payload"):
                result["payload"] = json.loads(result["payload"])
            if result.get("result"):
                result["result"] = json.loads(result["result"])
            return result
