"""Source credibility scoring helpers."""
from urllib.parse import urlparse
from typing import Optional


HIGH_TRUST_DOMAINS = {
    "archive.org",
    "britannica.com",
    "history.com",
    "loc.gov",
    "nasa.gov",
    "nih.gov",
    "noaa.gov",
    "si.edu",
    "wikipedia.org",
}


def score_source(url: Optional[str], content: Optional[str]) -> float:
    """Return a lightweight credibility score for a source."""
    score = 0.45
    domain = urlparse(url or "").netloc.lower().removeprefix("www.")

    if any(domain.endswith(trusted) for trusted in HIGH_TRUST_DOMAINS):
        score += 0.3
    if domain.endswith(".gov") or domain.endswith(".edu"):
        score += 0.25
    if content:
        length = len(content)
        if length > 1200:
            score += 0.1
        if length > 4000:
            score += 0.1

    return min(round(score, 2), 1.0)
