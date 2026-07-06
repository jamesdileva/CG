# Phase 3: Video Pipeline — API Reference

All endpoints under `/api/videos`

---

## `POST /api/videos/tts/{topic_id}`

Generate TTS audio for all scenes of a topic. Runs in the background.

**Response:**
```json
{
  "message": "TTS generation started",
  "topic_id": "uuid",
  "scenes_count": 8
}
```

---

## `GET /api/videos/tts/{topic_id}`

Get per-scene TTS status.

**Response:**
```json
{
  "topic_id": "uuid",
  "scenes": [
    { "id": "uuid", "order_index": 0, "has_audio": true, "audio_path": "data/projects/.../audio/scene-....mp3" }
  ]
}
```

---

## `POST /api/videos/images/{topic_id}`

Extract images from research sources. Runs in the background.

**Response:**
```json
{
  "message": "Image extraction started",
  "topic_id": "uuid"
}
```

---

## `GET /api/videos/assets/{topic_id}`

List all assets for a topic (images, audio, thumbnails).

**Query params:**
- `asset_type` — filter by type (`image`, `audio`, `thumbnail`)

**Response:**
```json
{
  "topic_id": "uuid",
  "assets": [
    {
      "id": "uuid",
      "type": "image",
      "file_path": "data/projects/.../images/img-01.jpg",
      "topic_id": "uuid",
      "scene_id": null,
      "source_url": "https://upload.wikimedia.org/...",
      "created_at": "2026-07-01T..."
    }
  ]
}
```

---

## `POST /api/videos/render/{topic_id}`

Render video for a topic. Uses TTS audio and images if available.

**Response:**
```json
{
  "message": "Video render started",
  "topic_id": "uuid",
  "video_id": "uuid",
  "job_id": "uuid"
}
```

---

## `POST /api/videos/thumbnail/{topic_id}`

Generate a thumbnail from the rendered video.

**Response:**
```json
{
  "message": "Thumbnail generated",
  "asset": { "id": "uuid", "type": "thumbnail", "file_path": "..." }
}
```

---

## `GET /api/videos/{topic_id}`

Get latest video render and scenes for a topic.

**Response:**
```json
{
  "topic_id": "uuid",
  "video": { "id": "uuid", "status": "RENDERED", "file_path": "...", ... },
  "scenes": [ { "id": "uuid", "order_index": 0, "text": "...", "duration": 8.0, "audio_path": "...", "image_path": null } ]
}
```
