"""Research API endpoints."""
from datetime import datetime
import logging
import uuid as _uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.core.config import settings
from backend.core.database import get_db
from backend.models.research import ResearchBundleResponse, ManualInputCreate
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.research.sources import collect_research, get_research_bundle, delete_research_source
from backend.research.extractor import extract_facts, extract_timeline
from backend.research.dedup import deduplicate_facts, conflict_check

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])
orchestrator = PipelineOrchestrator()


def _validate_uid(value: str, name: str) -> None:
    try:
        _uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid {name}: must be a valid UUID")


async def run_research_job(job_id: str, topic_id: str, max_sources: int) -> None:
    """Run and persist research for a topic."""
    try:
        await orchestrator.update_job(job_id, "RUNNING")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE jobs SET started_at = ?, updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), job_id),
            )
            conn.commit()

        await orchestrator.transition(topic_id, "RESEARCHING")
        bundle = await collect_research(topic_id, max_sources=max_sources)
        await orchestrator.transition(topic_id, "RESEARCH_COMPLETE")
        await orchestrator.update_job(
            job_id,
            "COMPLETE",
            result={
                "sources_count": len(bundle["sources"]),
                "facts_count": len(bundle["facts"]),
            },
        )
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE jobs SET completed_at = ?, updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), job_id),
            )
            conn.commit()
    except Exception as exc:
        logger.exception("Research job failed")
        await orchestrator.update_job(job_id, "FAILED", error=str(exc))


@router.post("/start/{topic_id}")
async def start_research(
    topic_id: str,
    background_tasks: BackgroundTasks,
    max_sources: int = 8,
):
    """Start research for an approved topic."""
    _validate_uid(topic_id, "topic_id")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM topics WHERE id = ?", (topic_id,))
        topic = cursor.fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic["status"] not in {"APPROVED", "RESEARCHING", "RESEARCH_COMPLETE", "SCRIPT_DRAFTED", "SCRIPT_APPROVED"}:
            raise HTTPException(
                status_code=400,
                detail="Topic must be approved before research can start",
            )

    job_id = await orchestrator.create_job(
        job_type="research",
        topic_id=topic_id,
        payload={"max_sources": max_sources},
    )
    background_tasks.add_task(run_research_job, job_id, topic_id, max_sources)
    return {"message": "Research started", "topic_id": topic_id, "job_id": job_id}


@router.post("/manual-input")
async def manual_research_input(body: ManualInputCreate):
    """Create a topic from pasted article text and extract facts/timeline without web scraping."""
    now = datetime.utcnow().isoformat()
    topic_id = str(_uuid.uuid4())
    source_id = str(_uuid.uuid4())

    with get_db() as conn:
        cursor = conn.cursor()
        # Create topic with APPROVED status (skip review)
        cursor.execute(
            """INSERT INTO topics (id, title, description, status, created_at, updated_at, approved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (topic_id, body.title, f"Manual research: {body.title[:100]}", "APPROVED", now, now, now),
        )

        # Store the pasted text as a single source
        cursor.execute(
            """INSERT INTO research_sources (id, topic_id, url, title, content, credibility_score, extracted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (source_id, topic_id, "manual://input", body.title, body.text, 0.7, now),
        )

    # Run extraction pipeline (same as web-scraped content)
    raw_facts = []
    for fact_text in extract_facts(body.text, limit=settings.research_fact_limit):
        raw_facts.append({"source_id": source_id, "fact": fact_text, "confidence": 0.7, "verified": True})

    # Deduplicate
    fact_texts = [f["fact"] for f in raw_facts]
    unique_texts = deduplicate_facts(fact_texts, threshold=0.85)
    kept_texts = set(unique_texts)

    stored_facts = []
    with get_db() as conn:
        cursor = conn.cursor()
        for fact in raw_facts:
            if fact["fact"] not in kept_texts:
                continue
            fact_id = str(_uuid.uuid4())
            cursor.execute(
                """INSERT INTO research_facts (id, topic_id, source_id, fact, confidence, verified, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fact_id, topic_id, source_id, fact["fact"], fact["confidence"], 1, now),
            )
            stored_facts.append({
                "id": fact_id, "topic_id": topic_id, "source_id": source_id,
                "fact": fact["fact"], "confidence": fact["confidence"],
                "verified": True, "created_at": now,
            })
        conn.commit()

    source_record = {
        "id": source_id, "topic_id": topic_id, "url": "manual://input",
        "title": body.title, "content": body.text[:500],
        "credibility_score": 0.7, "extracted_at": now,
    }

    return {
        "topic_id": topic_id,
        "sources": [source_record],
        "facts": stored_facts,
        "timeline": extract_timeline(stored_facts),
        "conflicts": conflict_check(stored_facts),
    }


@router.delete("/source/{source_id}")
async def delete_source(source_id: str):
    """Delete a research source and all facts extracted from it."""
    _validate_uid(source_id, "source_id")
    if not delete_research_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return {"message": "Source deleted", "source_id": source_id}


@router.get("/{topic_id}", response_model=ResearchBundleResponse)
async def get_research(topic_id: str):
    """Get stored research for a topic."""
    _validate_uid(topic_id, "topic_id")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Topic not found")

    return get_research_bundle(topic_id)
