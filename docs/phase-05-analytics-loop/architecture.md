# Phase 5: Analytics Loop — Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Dashboard UI                            │
│  [Summary Card: Total Views, Avg Score, Top Topic]           │
│  [Recent Performance Feed]                                   │
│  [Pipeline Status Stats]                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP REST
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI /api/analytics/*                     │
│                                                              │
│  POST /pull        GET /rankings                             │
│  POST /ingest      GET /{video_id}                           │
│  GET  /            (list all)                                │
└──────┬────────────────────────────┬──────────────────────────┘
       │                            │
       ▼                            ▼
┌──────────────┐          ┌─────────────────────┐
│  Puller       │          │  Ranker              │
│  (YouTube     │          │  (score calculation) │
│   Data API)   │          │                     │
└──────┬───────┘          └────────┬────────────┘
       │                           │
       ▼                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   Database (SQLite)                           │
│  analytics table: video_id, views, likes, comments, ...      │
│  topics table:   interest_score, uniqueness_score,           │
│                  source_score, category, published_at        │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### Analytics Pull
```
POST /api/analytics/pull
  → Query all youtube_uploads with youtube_id
  → For each: YouTube Data API videos.list(part="statistics")
  → Upsert into analytics table
  → Run ranker.update_topic_scores()
  → Return ingested count
```

### Score Calculation
```
update_topic_scores():
  For each topic with analytics data:
    avg_score = AVG(views_weighted + likes_weighted + comments_rate)
    interest_score = avg_score * 0.7 + views_factor * 0.3

rank_topics(limit=10):
  SELECT id, title, interest_score
  FROM topics
  WHERE interest_score IS NOT NULL
  ORDER BY interest_score DESC

get_low_performers(threshold=25):
  Topics with interest_score < threshold
```

## File Layout

```
backend/
├── analytics/
│   ├── __init__.py
│   ├── puller.py        # YouTube Data API polling
│   └── ranker.py         # Score calculation + ranking
├── api/
│   └── analytics.py      # REST endpoints
├── video/
│   ├── renderer.py       # generate_ambient_audio(), _mix_audio()
│   └── tts.py            # rate parameter support
renderer/src/
├── pages/
│   ├── Dashboard.tsx     # Analytics summary + performance feed
│   └── Production.tsx    # TTS rate selector
│   └── Publish.tsx       # Upload progress polling
└── api/
    └── client.ts         # getAnalyticsRankings, pullAnalytics, getJobStatus
```
