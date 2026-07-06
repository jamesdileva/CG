# Phase 02 Database Schema

## `research_sources`

Stores cleaned source text and a credibility score.

Key columns:

- `id`
- `topic_id`
- `url`
- `title`
- `content`
- `credibility_score`
- `extracted_at`

## `research_facts`

Stores extracted fact candidates.

Key columns:

- `id`
- `topic_id`
- `source_id`
- `fact`
- `confidence`
- `verified`
- `created_at`
