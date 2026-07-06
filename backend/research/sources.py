"""Research persistence and orchestration helpers."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
import uuid

import httpx

from backend.core.config import settings
from backend.core.database import get_db

logger = logging.getLogger(__name__)
from backend.research.dedup import deduplicate_facts, conflict_check
from backend.research.extractor import extract_facts, extract_timeline
from backend.research.ranking import score_source
from backend.research.scraper import build_source_candidates, scrape_url, ScrapedSource, _search_duckduckgo, _search_googlenews_rss, _fetch_wikipedia_internal_links


def _fallback_source(topic_title: str, topic_description: str | None) -> ScrapedSource:
    description = topic_description or "No description was available."
    content = (
        f"{topic_title}. {description} "
        "This local briefing was generated because live web sources were unavailable. "
        "Use it as a placeholder for drafting structure, then run research again with network access "
        "before approving a final documentary script."
    )
    return ScrapedSource(url="local://research-briefing", title=f"{topic_title} - Local briefing", content=content)


def clear_research(topic_id: str) -> None:
    """Delete existing research rows for a topic."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM research_facts WHERE topic_id = ?", (topic_id,))
        cursor.execute("DELETE FROM research_sources WHERE topic_id = ?", (topic_id,))
        conn.commit()


async def _fetch_related_wikipedia(topic_title: str, max_results: int = 6) -> list[ScrapedSource]:
    """Search Wikipedia for related articles and fetch their extracts.

    Searches both main Wikipedia and Simple Wikipedia to maximise content.
    Only includes articles whose content references the original topic title,
    excluding coincidental name collisions (e.g. game studios named after events).
    """
    from urllib.parse import quote_plus
    from backend.research.scraper import _extract_search_keywords, _WIKI_API_DELAY, _WIKI_API_HEADERS, _fetch_wikipedia_extract

    keywords = _extract_search_keywords(topic_title)
    if not keywords:
        return []

    results: list[ScrapedSource] = []
    seen_urls: set[str] = set()
    user_agent = _WIKI_API_HEADERS.get("User-Agent", "")

    async with httpx.AsyncClient(timeout=settings.research_scrape_timeout_seconds, follow_redirects=True) as client:
        # Search multiple query variations to find different relevant articles
        search_queries = [keywords]
        if not keywords.lower().startswith("history of"):
            search_queries.append(f"history of {keywords}")
        if not keywords.lower().startswith("timeline of"):
            search_queries.append(f"timeline of {keywords}")

        for search_query in search_queries:
            if len(results) >= max_results:
                break
            await asyncio.sleep(_WIKI_API_DELAY)
            search_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={quote_plus(search_query)}&format=json&srlimit=10&srwhat=text"
            )
            try:
                response = await client.get(search_url, headers=_WIKI_API_HEADERS)
                response.raise_for_status()
            except Exception as exc:
                logger.debug("Wikipedia search failed for %s: %s", search_query, exc)
                continue
            data = response.json()
            pages = data.get("query", {}).get("search", [])

            significant = {w for w in keywords.lower().split() if len(w) > 3}

            # Skip articles about companies, games, studios, etc. named after the topic
            _EXCLUDE_KEYWORDS = {"game", "studio", "llc", "inc", "company", "developer", "video game"}

            for page in pages:
                if len(results) >= max_results:
                    break
                title_lower = page["title"].lower()
                # Skip if the title looks like a company/game/studio named after the event
                if any(ex in title_lower for ex in _EXCLUDE_KEYWORDS):
                    logger.debug("Skipping corporate result: %s", page["title"])
                    continue
                # Require at least 1 significant keyword in the title (more lenient)
                matches = sum(1 for kw in significant if kw in title_lower)
                if matches < 1:
                    logger.debug("Skipping weakly related Wikipedia result: %s", page["title"])
                    continue

                extract = await _fetch_wikipedia_extract(client, page["title"], user_agent)
                if not extract:
                    continue
                if extract.url in seen_urls:
                    continue
                seen_urls.add(extract.url)

                # Verify the extract actually references the original topic (avoids name collisions)
                topic_lower = topic_title.lower()
                extract_lower = extract.content.lower()
                topic_words = {w for w in topic_lower.split() if len(w) > 3}
                # Require at least 1 topic word to appear in the extract content (more lenient)
                content_matches = sum(1 for w in topic_words if w in extract_lower)
                if content_matches < 1:
                    logger.debug("Skipping unrelated Wikipedia article: %s (does not reference %s)", page["title"], topic_title)
                    continue

                results.append(extract)
                await asyncio.sleep(_WIKI_API_DELAY)

        # Also try Simple Wikipedia for related articles
        if len(results) < max_results:
            await asyncio.sleep(_WIKI_API_DELAY)
            simple_search_url = (
                f"https://simple.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={quote_plus(keywords)}&format=json&srlimit=5&srwhat=text"
            )
            try:
                response = await client.get(simple_search_url, headers=_WIKI_API_HEADERS)
                response.raise_for_status()
                data = response.json()
                pages = data.get("query", {}).get("search", [])
                for page in pages:
                    if len(results) >= max_results:
                        break
                    extract = await _fetch_wikipedia_extract(
                        client, page["title"], user_agent,
                        api_base="https://simple.wikipedia.org/w/api.php",
                        wiki_base="https://simple.wikipedia.org/wiki/",
                    )
                    if not extract:
                        continue
                    if extract.url in seen_urls:
                        continue
                    seen_urls.add(extract.url)
                    results.append(extract)
                    await asyncio.sleep(_WIKI_API_DELAY)
            except Exception as exc:
                logger.debug("Simple Wikipedia search failed: %s", exc)

    return results


async def collect_research(topic_id: str, max_sources: int | None = None) -> dict:
    """Scrape, store, and extract facts for a topic."""
    if max_sources is None:
        max_sources = settings.research_max_sources
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, description FROM topics WHERE id = ?", (topic_id,))
        topic = cursor.fetchone()
        if not topic:
            raise ValueError("Topic not found")

    clear_research(topic_id)

    scraped_sources = []
    seen_urls = set()
    for url, title in build_source_candidates(topic["title"], max_sources=max_sources):
        try:
            source = await scrape_url(url, title)
        except Exception as exc:
            logger.warning("Failed to scrape %s: %s", url, exc)
            source = None
        if source:
            seen_urls.add(source.url.rstrip("/").lower())
            scraped_sources.append(source)

    remaining = max_sources - len(scraped_sources)

    # Try DuckDuckGo web search to find non-Wikipedia articles
    if remaining > 1:
        try:
            web_results = await _search_duckduckgo(topic["title"], max_results=remaining + 2)
            for w_url, w_title in web_results:
                if len(scraped_sources) >= max_sources:
                    break
                url_key = w_url.rstrip("/").lower()
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                try:
                    source = await scrape_url(w_url, w_title)
                except Exception as exc:
                    logger.debug("Failed to scrape DuckDuckGo result %s: %s", w_url, exc)
                    source = None
                if source:
                    scraped_sources.append(source)
        except Exception as exc:
            logger.warning("DuckDuckGo search failed: %s", exc)

    remaining = max_sources - len(scraped_sources)

    # Try Google News RSS for news articles about the topic
    if remaining > 1:
        try:
            news_results = await _search_googlenews_rss(topic["title"], max_results=remaining + 2)
            for n_url, n_title in news_results:
                if len(scraped_sources) >= max_sources:
                    break
                url_key = n_url.rstrip("/").lower()
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                try:
                    source = await scrape_url(n_url, n_title)
                except Exception as exc:
                    logger.debug("Failed to scrape Google News result %s: %s", n_url, exc)
                    source = None
                if source:
                    scraped_sources.append(source)
        except Exception as exc:
            logger.warning("Google News RSS search failed: %s", exc)

    remaining = max_sources - len(scraped_sources)

    # Try Wikipedia internal links for more related articles
    if remaining > 1:
        try:
            wiki_links = await _fetch_wikipedia_internal_links(topic["title"], max_results=remaining + 2)
            for w_url, w_title in wiki_links:
                if len(scraped_sources) >= max_sources:
                    break
                url_key = w_url.rstrip("/").lower()
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                try:
                    source = await scrape_url(w_url, w_title)
                except Exception as exc:
                    logger.debug("Failed to scrape Wikipedia link %s: %s", w_url, exc)
                    source = None
                if source:
                    scraped_sources.append(source)
        except Exception as exc:
            logger.warning("Wikipedia internal links fetch failed: %s", exc)

    remaining = max_sources - len(scraped_sources)

    # Supplement with related Wikipedia articles via API search
    if remaining > 0:
        try:
            extra = await _fetch_related_wikipedia(topic["title"], max_results=remaining + 2)
            for s in extra:
                if len(scraped_sources) >= max_sources:
                    break
                url_key = s.url.rstrip("/").lower()
                if url_key not in seen_urls:
                    seen_urls.add(url_key)
                    scraped_sources.append(s)
        except Exception as exc:
            logger.warning("Failed to fetch related Wikipedia articles: %s", exc)

    if not scraped_sources:
        scraped_sources.append(_fallback_source(topic["title"], topic["description"]))

    stored_sources = []
    raw_facts: list[dict] = []
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        for source in scraped_sources:
            source_id = str(uuid.uuid4())
            credibility = score_source(source.url, source.content)
            cursor.execute(
                """INSERT INTO research_sources
                   (id, topic_id, url, title, content, credibility_score, extracted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (source_id, topic_id, source.url, source.title, source.content, credibility, now),
            )
            stored_sources.append(
                {
                    "id": source_id,
                    "topic_id": topic_id,
                    "url": source.url,
                    "title": source.title,
                    "content": source.content,
                    "credibility_score": credibility,
                    "extracted_at": now,
                }
            )

            for fact in extract_facts(source.content, limit=settings.research_fact_limit):
                raw_facts.append(
                    {
                        "source_id": source_id,
                        "fact": fact,
                        "confidence": credibility,
                        "verified": credibility >= 0.7,
                    }
                )

        # Deduplicate facts before storing
        fact_texts = [f["fact"] for f in raw_facts]
        unique_texts = deduplicate_facts(fact_texts)
        kept_texts = set(unique_texts)
        deduped_facts = [f for f in raw_facts if f["fact"] in kept_texts]

        stored_facts = []
        for fact in deduped_facts:
            fact_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO research_facts
                   (id, topic_id, source_id, fact, confidence, verified, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fact_id, topic_id, fact["source_id"], fact["fact"], fact["confidence"], int(fact["verified"]), now),
            )
            stored_facts.append(
                {
                    "id": fact_id,
                    "topic_id": topic_id,
                    "source_id": fact["source_id"],
                    "fact": fact["fact"],
                    "confidence": fact["confidence"],
                    "verified": fact["verified"],
                    "created_at": now,
                }
            )

        conn.commit()

    return {
        "topic_id": topic_id,
        "sources": stored_sources,
        "facts": stored_facts,
        "timeline": extract_timeline(stored_facts),
        "conflicts": conflict_check(stored_facts),
    }


def delete_research_source(source_id: str) -> bool:
    """Delete a research source and all its associated facts. Returns True if deleted."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM research_facts WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM research_sources WHERE id = ?", (source_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_research_bundle(topic_id: str) -> dict:
    """Load stored research, facts, and derived timeline for a topic."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM research_sources WHERE topic_id = ? ORDER BY credibility_score DESC, extracted_at DESC",
            (topic_id,),
        )
        sources = [dict(row) for row in cursor.fetchall()]
        cursor.execute(
            "SELECT * FROM research_facts WHERE topic_id = ? ORDER BY confidence DESC, created_at DESC",
            (topic_id,),
        )
        facts = [dict(row) for row in cursor.fetchall()]

    return {
        "topic_id": topic_id,
        "sources": sources,
        "facts": facts,
        "timeline": extract_timeline(facts),
        "conflicts": conflict_check(facts),
    }
