# Phase 5: Analytics Loop — Database Schema

## New Columns on `topics` Table

```sql
ALTER TABLE topics ADD COLUMN interest_score REAL;
ALTER TABLE topics ADD COLUMN uniqueness_score REAL;
ALTER TABLE topics ADD COLUMN source_score REAL;
ALTER TABLE topics ADD COLUMN category TEXT;
ALTER TABLE topics ADD COLUMN published_at TIMESTAMP;
```

### Column Purpose

| Column | Type | Purpose |
|---|---|---|
| `interest_score` | REAL | 0–100, derived from analytics engagement + views |
| `uniqueness_score` | REAL | Reserved for future content uniqueness analysis |
| `source_score` | REAL | Reserved for source quality scoring |
| `category` | TEXT | Topic category (e.g., "history", "science") |
| `published_at` | TIMESTAMP | When the video was published on YouTube |

---

## Existing Table: `analytics`

Already existed (no schema changes).

```sql
CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    youtube_id TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    watch_time_seconds REAL DEFAULT 0,
    click_through_rate REAL DEFAULT 0,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);
```

### Key Queries

```sql
-- Get all analytics with video + topic info
SELECT a.*, v.topic_id, t.title AS topic_title
FROM analytics a
JOIN videos v ON v.id = a.video_id
JOIN topics t ON t.id = v.topic_id
ORDER BY a.ingested_at DESC;

-- Get analytics for a specific video
SELECT * FROM analytics WHERE video_id = ? ORDER BY ingested_at DESC LIMIT 1;

-- Rank topics by interest score
SELECT id, title, interest_score
FROM topics
WHERE interest_score IS NOT NULL
ORDER BY interest_score DESC
LIMIT 10;

-- Dashboard summary
SELECT
  SUM(a.views) AS total_views,
  AVG(t.interest_score) AS avg_score,
  COUNT(DISTINCT t.id) AS total_topics
FROM analytics a
JOIN videos v ON v.id = a.video_id
JOIN topics t ON t.id = v.topic_id;
```
