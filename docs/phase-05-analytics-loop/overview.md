# Phase 5: Analytics Loop — Overview

## Goal

Pull real YouTube analytics for uploaded videos, derive topic interest scores from performance data, and surface insights in the Dashboard — closing the feedback loop between publishing and future content decisions.

## What Was Built

### Backend

| Module | File | Purpose |
|---|---|---|
| Analytics Puller | `backend/analytics/puller.py` | Fetches views/likes/comments from YouTube Data API v3 |
| Analytics Ranker | `backend/analytics/ranker.py` | Blends analytics into interest scores, ranks topics, identifies low performers |
| Analytics API | `backend/api/analytics.py` | Endpoints for manual pull, rankings, ingest, and listing |
| DB Schema | `database/schema.sql` | Added score columns to `topics` table |

### Frontend

| Page | Updates |
|---|---|
| Dashboard (`Dashboard.tsx`) | Analytics summary card (total views, avg score, top topic), recent performance feed, pipeline status stats |

### Improvements (bundled with Phase 5)

| Feature | Files Changed |
|---|---|
| Background music | `backend/video/renderer.py` — FFmpeg-generated ambient audio |
| TTS speech rate | `backend/video/tts.py`, `backend/api/videos.py`, `Production.tsx` |
| Upload progress | `backend/api/publish.py`, `Publish.tsx` — async upload with job polling |

---

## Workflow

```
Upload video → YouTube (Phase 4)
        ↓
User clicks "Pull Analytics"
        ↓
POST /api/analytics/pull → fetches stats for all uploaded videos
        ↓
Stats ingested into analytics table
        ↓
Scores auto-updated via ranker
        ↓
Dashboard displays insights
```

## Key Decisions

- **Background music**: FFmpeg-generated ambient audio (110 Hz sine wave + pink noise at low volume), mixed behind TTS narration at 0.1 volume
- **TTS rate**: edge-tts `rate` parameter (`-30%` to `+30%`), selectable per-scene in Production page
- **Upload progress**: YouTube upload runs as async background task with job polling (2s interval)
- **Analytics pull**: YouTube Data API v3 `videos.list(part="statistics")` for all uploaded videos
- **Scoring**: Interest score = weighted blend of (views factor + avg engagement score), decayed per topic
