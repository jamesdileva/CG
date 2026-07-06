"""Deduplication for research facts and topics using TF-IDF + cosine similarity."""
from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def deduplicate_facts(facts: Sequence[str], threshold: float = SIMILARITY_THRESHOLD) -> list[str]:
    """Remove near-duplicate facts keeping the first occurrence."""
    if len(facts) < 2:
        return list(facts)

    cleaned = [f for f in facts if f]
    if not cleaned:
        return []

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf_matrix = vectorizer.fit_transform(cleaned)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except ValueError:
        return list(facts)

    keep = [True] * len(cleaned)
    for i in range(len(cleaned)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(cleaned)):
            if not keep[j]:
                continue
            if sim_matrix[i][j] >= threshold:
                keep[j] = False

    result = [cleaned[i] for i in range(len(cleaned)) if keep[i]]
    dropped = len(cleaned) - len(result)
    if dropped:
        logger.info(f"Deduplication dropped {dropped} of {len(cleaned)} facts")
    return result


def deduplicate_sources(
    urls: Sequence[str], threshold: float = SIMILARITY_THRESHOLD
) -> list[str]:
    """Deduplicate source URLs by similarity."""
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        normalized = url.strip().rstrip("/").lower()
        if normalized not in seen:
            seen.add(normalized)
            result.append(url)
    return result


def conflict_check(facts: list[dict]) -> list[dict]:
    """Detect contradictory facts by finding mutually exclusive claims.

    Only flags contradictions when both facts share the same year,
    reducing false positives from unrelated temporal references.
    """
    conflicts: list[dict] = []
    contradictory_pairs = [
        ("increased", "decreased"),
        ("rose", "fell"),
        ("grew", "shrank"),
        ("before", "after"),
        ("won", "lost"),
        ("discovered", "already known"),
        ("first", "earlier"),
    ]

    for i in range(len(facts)):
        text_i = (facts[i].get("fact") or "").lower()
        year_i = _find_year(facts[i])
        for j in range(i + 1, len(facts)):
            text_j = (facts[j].get("fact") or "").lower()
            year_j = _find_year(facts[j])
            for a, b in contradictory_pairs:
                if not ((a in text_i and b in text_j) or (b in text_i and a in text_j)):
                    continue
                # Require at least one fact to have a year (otherwise temporal words are innocuous)
                if not year_i and not year_j:
                    continue
                # Require same year to avoid false positives (e.g. "before 1919" vs "after 1908")
                if year_i and year_j and year_i != year_j:
                    continue
                # If only one fact has a year, the other is a general statement - not a contradiction
                if (year_i is None) != (year_j is None):
                    continue
                conflicts.append(
                    {
                        "fact_a": {"id": facts[i]["id"], "text": facts[i]["fact"]},
                        "fact_b": {"id": facts[j]["id"], "text": facts[j]["fact"]},
                        "reason": f"'{a}' vs '{b}'",
                        "year_a": year_i,
                        "year_b": year_j,
                    }
                )

    return conflicts


def _find_year(fact: dict) -> str | None:
    import re
    match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", fact.get("fact") or "")
    return match.group(0) if match else None
