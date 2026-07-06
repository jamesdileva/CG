# Phase 4: YouTube Integration — Database Schema

## Existing Table: `youtube_uploads`

No schema changes in Phase 4. The `youtube_uploads` table already supports all Phase 4 needs.

```sql
CREATE TABLE IF NOT EXISTS youtube_uploads (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    youtube_id TEXT,
    title TEXT,
    description TEXT,
    tags TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);
```

### Status Flow

```
PENDING → METADATA_READY → READY_TO_UPLOAD → UPLOADED
                                              UPLOAD_FAILED
```

### Key Queries

```sql
-- Find uploads ready for YouTube
SELECT yu.*, v.file_path, v.topic_id
FROM youtube_uploads yu
JOIN videos v ON v.id = yu.video_id
WHERE yu.status = 'READY_TO_UPLOAD';

-- Get thumbnail for a topic
SELECT * FROM assets
WHERE topic_id = ? AND type = 'thumbnail'
ORDER BY created_at DESC LIMIT 1;

-- Mark upload complete
UPDATE youtube_uploads
SET status = 'UPLOADED', youtube_id = ?, uploaded_at = ?
WHERE id = ?;
```

## File System: OAuth Token

```
data/youtube_token.json   # OAuth2 credentials (not in DB)
```

This file stores the Google OAuth refresh token, allowing headless re-authentication without re-prompting the user.
