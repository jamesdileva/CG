# Phase 5: Analytics Loop — Code Examples

## 1. Pull Analytics and Update Scores

```python
# POST /api/analytics/pull
# Fetches YouTube stats for all uploaded videos
# Auto-updates interest_scores after ingestion

response = await client.post("/api/analytics/pull")
data = response.json()
print(f"Ingested {data['ingested_count']} records")
```

## 2. Get Rankings and Dashboard Summary

```python
# Direct usage of the ranker
from backend.analytics.ranker import get_dashboard_summary, rank_topics

summary = get_dashboard_summary()
print(f"Total views: {summary['total_views']}")
print(f"Avg score: {summary['average_interest_score']:.1f}")
print(f"Top topic: {summary['top_topic']}")

rankings = rank_topics(limit=5)
for topic in rankings:
    print(f"{topic['title']}: {topic['interest_score']:.0f}")
```

## 3. Generate Background Music

```python
from backend.video.renderer import generate_ambient_audio

path = generate_ambient_audio(
    duration=120.0,
    output_dir=Path("data/projects/abc123/video"),
)
# Returns: "data/projects/abc123/video/ambient.mp3"
# Pink noise at 0.05 + 110 Hz sine wave at 0.03, mixed at 0.1 volume
```

## 4. TTS with Speech Rate

```python
from backend.video.tts import generate_scene_audio

path = await generate_scene_audio(
    text="Hello world",
    topic_id="abc123",
    scene_id="scene-001",
    rate="+15%",  # Options: -30%, -15%, +0%, +15%, +30%
)
```

## 5. Full CLI Workflow

```bash
# 1. Pull analytics
curl -X POST http://localhost:8000/api/analytics/pull

# 2. Get rankings
curl http://localhost:8000/api/analytics/rankings

# 3. List all analytics
curl http://localhost:8000/api/analytics

# 4. Render with background music
curl -X POST "http://localhost:8000/api/videos/render/{topic_id}?background_music=true"

# 5. Generate TTS with custom rate
curl -X POST "http://localhost:8000/api/videos/tts/{topic_id}?rate=+15%"

# 6. Upload with progress
curl -X POST http://localhost:8000/api/publish/{upload_id}/upload-to-youtube
# Returns job_id — poll status:
curl http://localhost:8000/api/pipeline/jobs/{job_id}
```
