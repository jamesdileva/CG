# Phase 02 - Research System

Phase 02 adds a usable research pass between topic approval and script generation.

## Built

- `/api/research/start/{topic_id}` starts a research job for approved topics.
- `/api/research/{topic_id}` returns sources, facts, timeline items, and conflicts.
- Source scraping uses no-key public source candidates and `trafilatura`.
- Fact extraction is deterministic and local.
- Research Viewer UI shows sources, extracted facts, and timeline candidates.
- Script generation now includes stored research facts when they exist.

## Current Limits

- Source discovery is intentionally lightweight and does not use a paid search API.
- If network scraping fails, a local briefing source is stored so the pipeline can keep moving.
- Conflict detection is reserved for a later pass.
