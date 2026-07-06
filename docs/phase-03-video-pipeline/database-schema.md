# Phase 3: Video Pipeline — Database Schema

## New Table: `assets`

```sql
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('image', 'audio', 'thumbnail')),
    file_path TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    scene_id TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (scene_id) REFERENCES scenes(id)
);
```

### Columns

| Column | Type | Description |
|---|---|---|
| `id` | TEXT (UUID) | Primary key |
| `type` | TEXT | `image`, `audio`, or `thumbnail` |
| `file_path` | TEXT | Absolute path to the file on disk |
| `topic_id` | TEXT (UUID) | FK to `topics.id` |
| `scene_id` | TEXT (UUID) | FK to `scenes.id` (optional, null for thumbnails) |
| `source_url` | TEXT | Original URL for extracted images |
| `created_at` | TIMESTAMP | When the asset was stored |

## Existing Tables Used

### `scenes`
```sql
-- Added audio_path support
audio_path TEXT  -- populated by TTS generation
```

### `videos`
```sql
-- Existing, no changes
-- status values used: RENDERING, RENDERED, FAILED
```

## Indexes

```sql
-- For Phase 3 asset queries
CREATE INDEX IF NOT EXISTS idx_assets_topic_id ON assets(topic_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_scene_id ON assets(scene_id);
```

## File System Layout

```
data/projects/{topic_id}/
├── scenes.json            # Scene manifest
├── images/                # Extracted research images
│   ├── img-01.jpg
│   └── img-02.png
├── audio/                 # TTS-generated narration
│   └── scene-{id}.mp3
└── video/
    ├── scenes/            # Per-scene rendered clips
    │   ├── scene-000.mp4
    │   └── scene-001.mp4
    ├── concat.txt         # FFmpeg concat demuxer file
    ├── documentary-mvp.mp4 # Final rendered video
    └── thumbnail.jpg       # Extracted thumbnail
```
