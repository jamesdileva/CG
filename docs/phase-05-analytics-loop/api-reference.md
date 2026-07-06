# Phase 5: Analytics Loop — API Reference

All endpoints under `/api/analytics`

---

## Analytics

### `POST /api/analytics/pull`

Fetch fresh YouTube analytics for all uploaded videos and update scores.

**Response:**
```json
{
  "message": "Analytics pulled and scores updated",
  "ingested_count": 3,
  "topic_ids_updated": ["uuid-1", "uuid-2"]
}
```

### `GET /api/analytics/rankings`

Get sorted topic rankings and a dashboard summary.

**Response:**
```json
{
  "rankings": [
    { "id": "uuid", "title": "Topic A", "interest_score": 82.5 }
  ],
  "low_performers": [
    { "id": "uuid", "title": "Topic B", "interest_score": 12.3 }
  ],
  "dashboard_summary": {
    "total_views": 15342,
    "average_interest_score": 45.2,
    "top_topic": "Topic A",
    "total_videos_analysed": 3
  }
}
```

### `POST /api/analytics/ingest`

Manually insert an analytics record.

**Body:**
```json
{
  "video_id": "uuid",
  "youtube_id": "dQw4w9WgXcQ",
  "views": 1500,
  "likes": 120,
  "comments": 45,
  "watch_time_seconds": 48000,
  "click_through_rate": 0.08
}
```

**Response:**
```json
{ "message": "Analytics ingested", "id": 1 }
```

### `GET /api/analytics/{video_id}`

Get analytics for a specific video.

### `GET /api/analytics`

List all analytics records (with optional `?limit=10`).

---

## Video Pipeline (additions)

### `POST /api/videos/tts/{topic_id}?rate=+0%`

Generate TTS audio with configurable speech rate. Rate values: `-30%`, `-15%`, `+0%`, `+15%`, `+30%`.

### `POST /api/videos/render/{topic_id}?background_music=true`

Render video with optional FFmpeg-generated ambient background music.

---

## Pipeline Jobs

### `GET /api/pipeline/jobs/{job_id}`

Get job status (used for upload progress tracking).

**Response:**
```json
{
  "id": "job-uuid",
  "status": "RUNNING",
  "type": "youtube_upload",
  "result": null,
  "error": null,
  "created_at": "..."
}
```
