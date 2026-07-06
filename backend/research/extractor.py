"""Simple deterministic fact and timeline extraction."""
from __future__ import annotations

import re


YEAR_PATTERN = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


# Strip wiki markup artifacts that survive explaintext mode
_WIKI_CLEANUP = re.compile(r"\[edit[^\]]*\]|\[\d+(?:[:\-,]\s*\d+(?:[–\-,\s]\s*\d+)*)*\]|\[[a-zA-Z]\]")


def extract_facts(content: str, limit: int = 60) -> list[str]:
    """Extract documentary-friendly fact candidates from source text."""
    clean_content = " ".join((content or "").split())
    if not clean_content:
        return []

    # Strip [edit], citation refs [1], [7]: 91, 95, and footnote markers [a] [b]
    clean_content = _WIKI_CLEANUP.sub("", clean_content)

    candidates = []
    for sentence in SENTENCE_PATTERN.split(clean_content):
        sentence = sentence.strip()
        if len(sentence) < 30 or len(sentence) > 500:
            continue
        has_specificity = bool(YEAR_PATTERN.search(sentence)) or any(
            token in sentence.lower()
            for token in (
                "because", "according", "during", "after", "before",
                "caused", "led to", "until", "since", "following",
                "including", "between", "discovered", "created",
                "resulted", "impact", "developed",
            )
        )
        if has_specificity and sentence not in candidates:
            candidates.append(sentence)
        if len(candidates) >= limit:
            break

    return candidates


def extract_timeline(facts: list[dict]) -> list[dict]:
    """Build a compact timeline from extracted facts."""
    timeline = []
    seen = set()
    for fact in facts:
        text = fact.get("fact", "")
        for year in YEAR_PATTERN.findall(text):
            key = (year, text)
            if key in seen:
                continue
            timeline.append(
                {
                    "year": year,
                    "fact": text,
                    "source_id": fact.get("source_id"),
                }
            )
            seen.add(key)

    return sorted(timeline, key=lambda item: item["year"])
