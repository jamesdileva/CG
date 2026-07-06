"""Web scraping utilities for Phase 2 research."""
from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

import httpx
import trafilatura

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Browser-like default headers to avoid being blocked by scrapers
_BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

_WIKI_API_DELAY = 2.0  # seconds between Wikipedia API calls to avoid rate limiting
_WIKI_API_HEADERS = {
    "User-Agent": "AIDocumentaryStudio/0.1 (research; https://github.com/user/ai-documentary-studio)",
    "Accept": "application/json",
}

_WIKI_SCRAPE_DELAY = 4.0  # seconds between HTML scrapes of Wikipedia pages


@dataclass
class ScrapedSource:
    url: str
    title: str
    content: str


# Words to strip from topic titles when searching Wikipedia
_FILLER_WORDS = re.compile(
    r"\b(the|a|an|of|in|on|at|for|to|and|or|is|was|story|history|truth|"
    r"amazing|incredible|untold|forgotten|secret|real|inside|great)\b",
    re.IGNORECASE,
)


def _extract_search_keywords(topic_title: str) -> str:
    """Strip filler words from a descriptive title to get core search terms."""
    cleaned = _FILLER_WORDS.sub("", topic_title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if len(cleaned) > 3 else topic_title


async def _retry_httpx_get(
    client: httpx.AsyncClient,
    url: str,
    headers: dict | None = None,
    max_retries: int = 3,
    base_delay: float = 3.0,
) -> httpx.Response:
    """GET with exponential backoff retry. Returns response or raises."""
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", str(base_delay * (attempt + 1))))
                logger.debug("Rate limited (429) on %s, retrying in %ds", url, retry_after)
                await asyncio.sleep(retry_after)
                continue
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (403, 404):
                raise  # Don't retry on auth/not-found
            last_exc = exc
            wait = base_delay * (2 ** attempt) + random.uniform(0, 2)
            logger.debug("HTTP error %d on %s, retrying in %.1fs", exc.response.status_code, url, wait)
            await asyncio.sleep(wait)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            wait = base_delay * (2 ** attempt) + random.uniform(0, 2)
            logger.debug("Connection error on %s (attempt %d/%d), retrying in %.1fs", url, attempt + 1, max_retries, wait)
            await asyncio.sleep(wait)
    raise last_exc or RuntimeError(f"Failed to fetch {url}")


async def _fetch_wikipedia_extract(
    client: httpx.AsyncClient, titles: str, user_agent: str,
    api_base: str = "https://en.wikipedia.org/w/api.php",
    wiki_base: str = "https://en.wikipedia.org/wiki/",
) -> Optional[ScrapedSource]:
    """Fetch a Wikipedia extract by exact title via the API."""
    await asyncio.sleep(_WIKI_API_DELAY)
    api_url = (
        f"{api_base}?action=query&prop=extracts&explaintext"
        f"&titles={quote_plus(titles)}&format=json&redirects=1"
    )
    response = await client.get(api_url, headers=_WIKI_API_HEADERS)
    response.raise_for_status()
    data = response.json()

    pages_data = data.get("query", {}).get("pages", {})
    if not pages_data:
        return None

    page_id, page = next(iter(pages_data.items()))
    if page_id == "-1":
        return None

    extract = page.get("extract", "")
    if len(extract.strip()) < 120:
        return None

    page_title = page.get("title", titles)
    source_label = "Simple Wikipedia" if "simple" in wiki_base else "Wikipedia"
    page_url = f"{wiki_base}{quote_plus(page_title.replace(' ', '_'))}"
    content = " ".join(extract.split())[:settings.research_content_max_chars + 5000]
    return ScrapedSource(url=page_url, title=f"{page_title} - {source_label}", content=content)


async def _search_wikipedia(
    client: httpx.AsyncClient, query: str, user_agent: str
) -> Optional[ScrapedSource]:
    """Search Wikipedia and return extract of the top relevant result."""
    await asyncio.sleep(_WIKI_API_DELAY)
    search_url = (
        f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(query)}"
        f"&format=json&srlimit=5&srwhat=text"
    )
    response = await client.get(search_url, headers=_WIKI_API_HEADERS)
    response.raise_for_status()
    data = response.json()

    pages = data.get("query", {}).get("search", [])
    if not pages:
        return None

    # Extract significant keywords from query for relevance checking
    query_lower = query.lower()
    significant = {w for w in _extract_search_keywords(query).lower().split() if len(w) > 3}

    # Try each search result until we get a valid extract with relevance
    for page in pages:
        title_lower = page["title"].lower()
        if significant and not any(kw in title_lower for kw in significant):
            logger.debug("Skipping irrelevant Wikipedia result: %s", page["title"])
            continue
        result = await _fetch_wikipedia_extract(client, page["title"], user_agent)
        if result:
            return result

    return None


async def _scrape_wikipedia(topic_title: str, title_hint: str) -> Optional[ScrapedSource]:
    """Scrape Wikipedia. Tries exact URL first, then API with exact title, then search."""
    user_agent = random.choice(_USER_AGENTS)

    # Determine if this is Simple Wikipedia based on title hint
    is_simple = "Simple Wikipedia" in title_hint
    wiki_domain = "https://simple.wikipedia.org" if is_simple else "https://en.wikipedia.org"
    wiki_api = f"{wiki_domain}/w/api.php"
    wiki_base = f"{wiki_domain}/wiki/"

    # Step 1: Try exact URL via HTML scraping (with browser headers + retry)
    await asyncio.sleep(_WIKI_SCRAPE_DELAY)  # Be polite between Wikipedia scrapes
    slug = topic_title.strip().replace(" ", "_")
    exact_url = f"{wiki_domain}/wiki/{quote_plus(slug)}"
    async with httpx.AsyncClient(timeout=settings.research_scrape_timeout_seconds, follow_redirects=True) as client:
        try:
            wiki_headers = {**_BROWSER_HEADERS, "User-Agent": user_agent}
            response = await _retry_httpx_get(client, exact_url, headers=wiki_headers)
            extracted = trafilatura.extract(response.text, include_comments=False, include_tables=False)
            content = extracted or response.text
            content = " ".join(content.split())
            if len(content) >= 120:
                return ScrapedSource(url=str(response.url), title=title_hint, content=content[:settings.research_content_max_chars])
        except Exception as exc:
            logger.debug("Wikipedia HTML scrape failed for %s: %s", exact_url, exc)

        # Step 2: Try API with exact title (handles redirects, near-matches)
        await asyncio.sleep(_WIKI_API_DELAY)
        result = await _fetch_wikipedia_extract(client, topic_title, user_agent, api_base=wiki_api, wiki_base=wiki_base)
        if result:
            return result

        # Step 3: Try search with cleaned-up keywords
        keywords = _extract_search_keywords(topic_title)
        if keywords != topic_title:
            result = await _search_wikipedia(client, keywords, user_agent)
            if result:
                return result

        # Step 4: Fall back to full-title search
        result = await _search_wikipedia(client, topic_title, user_agent)
        if result:
            return result

    return None


async def _search_duckduckgo(topic_title: str, max_results: int = 5) -> list[tuple[str, str]]:
    """Search DuckDuckGo for articles about the topic. Returns (url, title) pairs.

    Uses the ddgs library which handles CAPTCHA challenges and returns clean results.
    Filters out Wikipedia results to avoid duplication.
    """
    from urllib.parse import urlparse
    from ddgs import DDGS

    results: list[tuple[str, str]] = []
    try:
        ddgs_results = await asyncio.to_thread(
            lambda: list(DDGS().text(topic_title, max_results=max_results + 2))
        )
        for r in ddgs_results:
            if len(results) >= max_results:
                break
            url = r.get("href", "").strip()
            title = r.get("title", "").strip()
            if not url or not title:
                continue
            domain = urlparse(url).netloc.lower()
            if "wikipedia.org" in domain:
                continue
            if any(d in domain for d in ("duckduckgo.com", "youtube.com", "reddit.com")):
                continue
            results.append((url, title))
    except Exception as exc:
        logger.debug("DuckDuckGo search failed for '%s': %s", topic_title, exc)

    logger.info("DuckDuckGo found %d results for '%s'", len(results), topic_title)
    return results


async def _fetch_wikipedia_internal_links(topic_title: str, max_results: int = 5) -> list[tuple[str, str]]:
    """Find related Wikipedia pages by fetching internal links from the main article.

    Gets the list of linked pages from a Wikipedia article and returns
    the most relevant ones (skipping navigation templates, disambiguation, etc.).
    """
    from urllib.parse import urlparse

    slug = topic_title.strip().replace(" ", "_")
    api_url = (
        f"https://en.wikipedia.org/w/api.php?action=query&prop=links"
        f"&titles={quote_plus(slug)}&format=json&pllimit=50"
        f"&plnamespace=0"  # article namespace only
    )

    results: list[tuple[str, str]] = []
    seen_titles: set[str] = set()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            await asyncio.sleep(_WIKI_API_DELAY)
            response = await client.get(api_url, headers=_WIKI_API_HEADERS)
            response.raise_for_status()
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                links = page_data.get("links", [])
                for link in links:
                    title = link.get("title", "")
                    title_lower = title.lower()
                    # Skip common boilerplate / list / disambig pages
                    if any(
                        title_lower.startswith(prefix)
                        for prefix in ("list of", "wikipedia:", "template:", "category:", "help:", "portal:", "book:")
                    ):
                        continue
                    # Skip if it's the same as the topic
                    if title_lower == topic_title.lower():
                        continue
                    # Skip if already seen
                    if title.lower() in seen_titles:
                        continue
                    seen_titles.add(title.lower())

                    link_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    results.append((link_url, f"{title} - Wikipedia"))
                    if len(results) >= max_results:
                        break
                break  # Only process the main page
        except Exception as exc:
            logger.debug("Wikipedia internal links fetch failed for '%s': %s", topic_title, exc)

    return results


async def _search_googlenews_rss(topic_title: str, max_results: int = 5) -> list[tuple[str, str]]:
    """Search Google News RSS for articles about the topic. Returns (url, title) pairs.

    Free, no API key needed. Filters out Wikipedia, YouTube, Reddit results.
    """
    from urllib.parse import urlparse
    import xml.etree.ElementTree as ET

    results: list[tuple[str, str]] = []
    search_query = quote_plus(topic_title)
    rss_url = (
        f"https://news.google.com/rss/search?q={search_query}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await _retry_httpx_get(client, rss_url)
            if response.status_code != 200:
                logger.debug("Google News RSS returned %s for '%s'", response.status_code, topic_title)
                return results

            root = ET.fromstring(response.text)
            # RSS structure: rss > channel > item (title, link, source)
            for item in root.iter("item"):
                if len(results) >= max_results:
                    break
                link_el = item.find("link")
                title_el = item.find("title")
                if link_el is None or title_el is None:
                    continue
                url = link_el.text.strip() if link_el.text else ""
                title = title_el.text.strip() if title_el.text else ""
                if not url or not title:
                    continue
                domain = urlparse(url).netloc.lower()
                if "wikipedia.org" in domain:
                    continue
                if any(d in domain for d in ("youtube.com", "reddit.com", "google.com")):
                    continue
                results.append((url, title))
    except Exception as exc:
        logger.debug("Google News RSS search failed for '%s': %s", topic_title, exc)

    logger.info("Google News RSS found %d results for '%s'", len(results), topic_title)
    return results


def build_source_candidates(topic_title: str, max_sources: int = 8) -> list[tuple[str, str]]:
    """Build source candidates for a documentary topic.

    Only uses sources that return actual article content (not search result pages).
    Wikipedia and Simple Wikipedia are guaranteed to return usable text.
    Additional related articles are discovered at fetch time via Wikipedia API.
    """
    slug = topic_title.strip().replace(" ", "_")
    encoded_slug = quote_plus(slug)

    candidates = [
        (f"https://en.wikipedia.org/wiki/{encoded_slug}", f"{topic_title} - Wikipedia"),
        (f"https://simple.wikipedia.org/wiki/{encoded_slug}", f"{topic_title} - Simple Wikipedia"),
    ]
    return candidates[:max_sources]


async def scrape_url(url: str, title_hint: str) -> Optional[ScrapedSource]:
    """Fetch a URL and extract readable text.

    For Wikipedia, uses a multi-step fallback: HTML scrape -> API exact title -> API search.
    For other URLs, uses browser-like headers and retry with exponential backoff.
    """
    if "wikipedia.org" in url and "/wiki/" in url:
        topic_title = title_hint.replace(" - Wikipedia", "").replace(" - Simple Wikipedia", "").strip()
        result = await _scrape_wikipedia(topic_title, title_hint)
        if result:
            return result
        return None

    user_agent = random.choice(_USER_AGENTS)
    headers = {**_BROWSER_HEADERS, "User-Agent": user_agent}

    async with httpx.AsyncClient(timeout=settings.research_scrape_timeout_seconds, follow_redirects=True) as client:
        response = await _retry_httpx_get(client, url, headers=headers)

    extracted = trafilatura.extract(response.text, include_comments=False, include_tables=False)
    content = extracted or response.text
    content = " ".join(content.split())
    if len(content) < 120:
        return None

    return ScrapedSource(url=str(response.url), title=title_hint, content=content[:settings.research_content_max_chars])

