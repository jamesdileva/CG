from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote_plus

import httpx

from backend.core.database import get_db

logger = logging.getLogger(__name__)

PROJECTS_DIR = Path(__file__).parent.parent.parent / "data" / "projects"

_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_MAX_IMAGES_PER_SOURCE = 5
_MAX_FILE_SIZE = 2 * 1024 * 1024
_TOTAL_TIMEOUT = 60.0
_PER_PAGE_TIMEOUT = 8.0
_PER_IMAGE_TIMEOUT = 8.0

_WIKI_API_HEADERS = {
    "User-Agent": "AIDocumentaryStudio/0.1 (research; https://github.com/user/ai-documentary-studio)",
    "Accept": "application/json",
}


def _is_image_url(url: str) -> bool:
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    return ext in _EXTENSIONS


_IMAGE_MAGIC: list[tuple[bytes, int]] = [
    (b"\xff\xd8\xff", 0),       # JPEG
    (b"\x89PNG", 0),            # PNG
    (b"GIF8", 0),               # GIF
    (b"RIFF", 0),               # WebP (RIFF....WEBP)
]


def _is_valid_image_file(path: Path) -> bool:
    """Check file starts with known image magic bytes (rejects HTML error pages saved as .jpg)."""
    if not path.exists() or path.stat().st_size < 512:
        return False
    try:
        with path.open("rb") as f:
            head = f.read(16)
        for magic, offset in _IMAGE_MAGIC:
            if head[offset:offset + len(magic)] == magic:
                if magic == b"RIFF" and head[8:12] != b"WEBP":
                    continue
                return True
    except Exception:
        pass
    return False


def _extract_wiki_title(url: str) -> str | None:
    """Extract Wikipedia page title from a URL."""
    match = re.search(r"/wiki/([^?#]+)", url)
    if not match:
        return None
    return match.group(1).replace("_", " ")


async def _fetch_wiki_page_images(client: httpx.AsyncClient, page_title: str, page_url: str) -> tuple[list[dict], str]:
    """Get all image URLs + captions from a Wikipedia page via the API (2 calls total).

    Returns ([{"url": str, "caption": str}, ...], referer).
    """
    images: list[dict] = []
    params = {
        "action": "query",
        "titles": page_title,
        "prop": "images",
        "format": "json",
        "imlimit": "10",
        "redirects": "1",
    }
    response = await client.get(
        "https://en.wikipedia.org/w/api.php",
        params=params,
        headers=_WIKI_API_HEADERS,
    )
    response.raise_for_status()
    data = response.json()
    pages = data.get("query", {}).get("pages", {})
    file_titles: list[str] = []
    for page_id, page in pages.items():
        if page_id == "-1":
            continue
        for img in page.get("images", []):
            title = img.get("title", "")
            if title.startswith("File:"):
                file_titles.append(title)

    if not file_titles:
        return [], f"https://en.wikipedia.org/wiki/{quote_plus(page_title.replace(' ', '_'))}"

    # Batch-fetch all image URLs + metadata in one call
    await asyncio.sleep(0.5)
    urls_params = {
        "action": "query",
        "titles": "|".join(file_titles),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    resp2 = await client.get(
        "https://en.wikipedia.org/w/api.php",
        params=urls_params,
        headers=_WIKI_API_HEADERS,
    )
    resp2.raise_for_status()
    img_data = resp2.json()
    for p_id, p_data in img_data.get("query", {}).get("pages", {}).items():
        if p_id == "-1":
            continue
        for info in p_data.get("imageinfo", []):
            url = info.get("url", "")
            if not url or not _is_image_url(url):
                continue
            caption = ""
            extmeta = info.get("extmetadata") or {}
            raw = extmeta.get("ImageDescription", {}).get("value", "")
            if raw:
                caption = re.sub(r"<[^>]+>", "", raw).strip()
                if len(caption) > 200:
                    caption = caption[:197] + "..."
            images.append({"url": url, "caption": caption})

    return images, f"https://en.wikipedia.org/wiki/{quote_plus(page_title.replace(' ', '_'))}"


async def _download_image(client: httpx.AsyncClient, url: str, images_dir: Path, seen_urls: set[str], count: int, referer: str | None = None, caption: str = "") -> dict | None:
    if url in seen_urls:
        return None
    if not _is_image_url(url):
        return None
    seen_urls.add(url)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Origin": "https://en.wikipedia.org",
        }
        if referer:
            headers["Referer"] = referer
        img_response = await asyncio.wait_for(
            client.get(url, headers=headers),
            timeout=_PER_IMAGE_TIMEOUT,
        )

        content = img_response.content

        # If Wikimedia blocks httpx (TLS fingerprint), fall back to curl.exe (uses native Windows TLS)
        if img_response.status_code == 403:
            import subprocess
            import shutil
            curl = shutil.which("curl.exe") or shutil.which("curl")
            if curl:
                parsed = urlparse(url)
                ext = Path(parsed.path).suffix.lower() or ".jpg"
                filename = f"img-{count + 1:02d}{ext}"
                filepath = images_dir / filename
                # Download to temp file first to avoid leaving corrupt data on disk
                tmppath = images_dir / f".{filename}.tmp"
                curl_cmd = [
                    curl, "-s", "-L", "-o", str(tmppath), "-w", "%{http_code}",
                    "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ]
                if referer:
                    curl_cmd += ["-e", referer]
                curl_cmd.append(url)

                logger.info("httpx 403, trying curl.exe fallback for %s", url)
                try:
                    proc = await asyncio.wait_for(
                        asyncio.to_thread(subprocess.run, curl_cmd, capture_output=True, text=True, timeout=_PER_IMAGE_TIMEOUT),
                        timeout=_PER_IMAGE_TIMEOUT + 2.0,
                    )
                    http_code = proc.stdout.strip() if proc.stdout else ""
                    if (proc.returncode == 0 and http_code == "200"
                            and _is_valid_image_file(tmppath)):
                        # replace() overwrites destination, rename() fails on Win32 if exists
                        tmppath.replace(filepath)
                        logger.info("curl.exe succeeded for %s", url)
                        return {
                            "file_path": str(filepath),
                            "source_url": url,
                            "topic_id": images_dir.parent.name,
                            "caption": caption,
                        }
                    else:
                        logger.warning("curl.exe failed for %s: code=%s ret=%d err=%s", url, http_code, proc.returncode, (proc.stderr or "")[:200])
                        if tmppath.exists():
                            tmppath.unlink()
                except Exception as curl_err:
                    logger.warning("curl.exe exception for %s: %s", url, curl_err)
                    if tmppath.exists():
                        tmppath.unlink()
            else:
                logger.warning("curl.exe not found, skipping 403 image: %s", url)
            return None

        img_response.raise_for_status()

        if len(content) > _MAX_FILE_SIZE or len(content) < 512:
            return None

        parsed = urlparse(url)
        ext = Path(parsed.path).suffix.lower() or ".jpg"
        filename = f"img-{count + 1:02d}{ext}"
        filepath = images_dir / filename
        filepath.write_bytes(content)

        return {
            "file_path": str(filepath),
            "source_url": url,
            "topic_id": images_dir.parent.name,
            "caption": caption,
        }
    except Exception:
        return None


async def _extract_from_source(client: httpx.AsyncClient, source_url: str, images_dir: Path, seen_urls: set[str]) -> list[dict]:
    if not source_url.startswith("http"):
        return []

    # For Wikipedia sources, use the API to get images (avoids 403 on HTML scrape)
    wiki_title = _extract_wiki_title(source_url)
    if wiki_title:
        image_infos, referer = await _fetch_wiki_page_images(client, wiki_title, source_url)
        tasks = []
        for img_info in image_infos:
            if len(tasks) >= _MAX_IMAGES_PER_SOURCE:
                break
            url = img_info["url"]
            if url in seen_urls:
                continue
            caption = img_info.get("caption", "")
            tasks.append(_download_image(client, url, images_dir, seen_urls, len(tasks), referer, caption))
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    # Fallback: scrape HTML for images
    try:
        response = await asyncio.wait_for(
            client.get(source_url, headers={"User-Agent": "AIDocumentaryStudio/0.1"}),
            timeout=_PER_PAGE_TIMEOUT,
        )
        response.raise_for_status()
    except Exception:
        return []

    html = response.text
    matches = _IMG_RE.findall(html)

    tasks = []
    count = 0
    for src in matches:
        if count >= _MAX_IMAGES_PER_SOURCE:
            break

        full_url = urljoin(source_url, src)
        if full_url in seen_urls:
            continue
        if not _is_image_url(full_url):
            continue

        tasks.append(_download_image(client, full_url, images_dir, seen_urls, count))
        count += 1

    results = await asyncio.gather(*tasks)
    return [r for r in results if r]


async def extract_images_for_topic(topic_id: str) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url FROM research_sources WHERE topic_id = ?",
            (topic_id,),
        )
        sources = [dict(row) for row in cursor.fetchall()]

    images_dir = PROJECTS_DIR / topic_id / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    try:
        async def _run():
            downloaded = []
            seen_urls: set[str] = set()

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                for source in sources:
                    results = await _extract_from_source(client, source["url"], images_dir, seen_urls)
                    downloaded.extend(results)

            return downloaded

        return await asyncio.wait_for(_run(), timeout=_TOTAL_TIMEOUT)
    except asyncio.TimeoutError:
        return []
