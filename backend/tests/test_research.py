"""Tests for Phase 2 research system."""
import pytest
from unittest.mock import AsyncMock, patch

from backend.research.dedup import deduplicate_facts, conflict_check, deduplicate_sources
from backend.research.extractor import extract_facts, extract_timeline
from backend.research.ranking import score_source
from backend.research.sources import collect_research, get_research_bundle, clear_research
from backend.research.scraper import build_source_candidates


class TestExtractor:
    def test_extract_facts_short_sentence_skipped(self):
        facts = extract_facts("Short.")
        assert facts == []

    def test_extract_facts_with_year(self):
        content = "The Battle of Waterloo was fought on June 18, 1815. This ended Napoleon's rule."
        facts = extract_facts(content)
        assert len(facts) >= 1
        assert "1815" in facts[0]

    def test_extract_facts_with_causal_keyword(self):
        content = "The recession was caused by the housing market collapse. " * 5
        facts = extract_facts(content)
        assert len(facts) > 0

    def test_extract_facts_limit(self):
        sentences = [
            "In 1776 the Declaration of Independence was signed by the thirteen colonies.",
            "During 1777 the Continental Army faced a difficult winter at Valley Forge.",
            "After 1778 France became a key ally providing military support to the revolution.",
            "In 1781 the British surrendered at Yorktown ending the major fighting.",
            "By 1783 the Treaty of Paris was signed recognizing American independence.",
            "In 1787 the Constitution was drafted at the Philadelphia Convention.",
        ] * 3
        content = " ".join(sentences)
        facts = extract_facts(content, limit=5)
        assert len(facts) == 5

    def test_extract_timeline_empty(self):
        assert extract_timeline([]) == []

    def test_extract_timeline_with_facts(self):
        facts = [
            {"fact": "The event happened in 1919.", "source_id": "s1"},
            {"fact": "It was rebuilt in 1925.", "source_id": "s2"},
        ]
        timeline = extract_timeline(facts)
        assert len(timeline) == 2
        assert timeline[0]["year"] == "1919"
        assert timeline[1]["year"] == "1925"

    def test_extract_timeline_sorts_by_year(self):
        facts = [
            {"fact": "In 1925 the city rebuilt.", "source_id": "s1"},
            {"fact": "In 1919 the flood happened.", "source_id": "s2"},
        ]
        timeline = extract_timeline(facts)
        assert timeline[0]["year"] == "1919"
        assert timeline[1]["year"] == "1925"


class TestRanking:
    def test_score_source_base(self):
        score = score_source("http://example.com", "short")
        assert score == 0.45

    def test_score_source_wikipedia_boost(self):
        score = score_source("http://en.wikipedia.org/wiki/Test", "word " * 200)
        assert score >= 0.75

    def test_score_source_gov_boost(self):
        score = score_source("http://www.nasa.gov/page", "word " * 200)
        assert score >= 0.8

    def test_score_source_content_length_boost(self):
        score = score_source("http://example.com", "word " * 500)
        assert score >= 0.55

    def test_score_source_caps_at_one(self):
        score = score_source("http://www.nasa.gov/page", "word " * 1000)
        assert score <= 1.0

    def test_score_source_empty_url(self):
        score = score_source(None, "some content")
        assert score == 0.45


class TestDedup:
    def test_dedup_facts_empty(self):
        assert deduplicate_facts([]) == []

    def test_dedup_facts_single(self):
        assert deduplicate_facts(["Only fact."]) == ["Only fact."]

    def test_dedup_facts_no_duplicates(self):
        facts = ["In 1919 the flood happened.", "In 1925 the city rebuilt."]
        result = deduplicate_facts(facts)
        assert len(result) == 2

    def test_dedup_facts_removes_duplicates(self):
        facts = [
            "The flood happened in 1919 in Boston.",
            "The flood happened in 1919 in Boston.",
            "In 1925 the city rebuilt the area.",
        ]
        result = deduplicate_facts(facts)
        assert len(result) == 2
        assert result == [
            "The flood happened in 1919 in Boston.",
            "In 1925 the city rebuilt the area.",
        ]

    def test_dedup_sources(self):
        urls = ["http://example.com/page", "http://EXAMPLE.com/page", "http://other.com"]
        result = deduplicate_sources(urls)
        assert len(result) == 2

    def test_conflict_check_empty(self):
        assert conflict_check([]) == []

    def test_conflict_check_contradictory_words(self):
        facts = [
            {"id": "1", "fact": "The population increased in 1919."},
            {"id": "2", "fact": "The population decreased in 1919."},
        ]
        conflicts = conflict_check(facts)
        assert len(conflicts) >= 1
        assert conflicts[0]["reason"] == "'increased' vs 'decreased'"

    def test_conflict_check_different_years_skipped(self):
        facts = [
            {"id": "1", "fact": "The population increased in 1919."},
            {"id": "2", "fact": "The population decreased in 1920."},
        ]
        assert conflict_check(facts) == []

    def test_conflict_check_one_year_missing_skipped(self):
        facts = [
            {"id": "1", "fact": "The population increased in 1919."},
            {"id": "2", "fact": "The population decreased."},
        ]
        assert conflict_check(facts) == []

    def test_conflict_check_no_conflict(self):
        facts = [
            {"id": "1", "fact": "The flood happened in 1919."},
            {"id": "2", "fact": "The city rebuilt in 1925."},
        ]
        assert conflict_check(facts) == []


class TestIntegration:
    @pytest.mark.asyncio
    async def test_collect_research_default_flow(self, sample_topic, mock_httpx):
        bundle = await collect_research(sample_topic, max_sources=2)
        assert bundle["topic_id"] == sample_topic
        assert len(bundle["sources"]) > 0
        assert len(bundle["facts"]) >= 0
        assert "conflicts" in bundle

    @pytest.mark.asyncio
    async def test_collect_research_no_network_fallback(self, sample_topic, mock_failed_httpx):
        bundle = await collect_research(sample_topic, max_sources=2)
        assert bundle["topic_id"] == sample_topic
        assert len(bundle["sources"]) == 1
        assert bundle["sources"][0]["url"] == "local://research-briefing"

    @pytest.mark.asyncio
    async def test_get_research_bundle_empty(self, sample_topic):
        bundle = get_research_bundle(sample_topic)
        assert bundle["topic_id"] == sample_topic
        assert bundle["sources"] == []
        assert bundle["facts"] == []

    @pytest.mark.asyncio
    async def test_collect_and_retrieve(self, sample_topic, mock_httpx):
        await collect_research(sample_topic, max_sources=2)
        bundle = get_research_bundle(sample_topic)
        assert len(bundle["sources"]) > 0
        assert len(bundle["facts"]) >= 0

    @pytest.mark.asyncio
    async def test_clear_research(self, sample_topic, mock_httpx):
        await collect_research(sample_topic, max_sources=2)
        clear_research(sample_topic)
        bundle = get_research_bundle(sample_topic)
        assert bundle["sources"] == []
        assert bundle["facts"] == []

    def test_build_source_candidates(self):
        candidates = build_source_candidates("Test Topic", max_sources=2)
        assert len(candidates) == 2
        for url, title in candidates:
            assert isinstance(url, str)
            assert isinstance(title, str)

    def test_build_source_candidates_max(self):
        candidates = build_source_candidates("Test Topic", max_sources=10)
        assert len(candidates) == 2  # Wikipedia + Simple Wikipedia
