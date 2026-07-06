# Phase 4: YouTube Integration — Architecture

## Component Diagram

```
┌─────────────────────────────────────────────┐
│              Publish Manager UI              │
│   [Sign in] [Metadata] [Approve] [Upload]   │
└──────────────────┬──────────────────────────┘
                   │ HTTP REST
                   ▼
┌──────────────────────────────────────────────┐
│           FastAPI /api/publish/*              │
│                                               │
│  /auth/url    /auth/callback  /auth/status    │
│  /metadata    /{id}/approve                   │
│  /{id}/upload-to-youtube                      │
└──────┬────────────────────────────┬───────────┘
       │                            │
       ▼                            ▼
┌──────────────┐          ┌─────────────────────┐
│  YouTube Auth │          │  YouTube Uploader   │
│  (OAuth 2.0)  │          │  (Data API v3)      │
└──────┬───────┘          └────────┬────────────┘
       │                           │
       ▼                           ▼
┌──────────────────────────────────────────────┐
│              Google APIs (HTTPS)              │
│  - OAuth 2.0 token endpoint                   │
│  - YouTube Data API v3                        │
│    - /youtube/v3/videos?part=snippet,status   │
│    - /youtube/v3/thumbnails/set               │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│              File System                      │
│  data/youtube_token.json  ← persisted OAuth  │
└──────────────────────────────────────────────┘
```

## Data Flow

### OAuth Authentication
```
GET /api/publish/auth/url
  → flow.authorization_url() → returns URL
  → User opens URL in browser
  → Grants consent → receives code
  → POST /api/publish/auth/callback { code }
    → flow.fetch_token(code) → save_credentials()
    → Token persisted to data/youtube_token.json
```

### YouTube Upload
```
POST /api/publish/{upload_id}/upload-to-youtube
  → Load upload record + video path from DB
  → Load thumbnail from assets (Phase 3)
  → Load OAuth credentials from youtube_token.json
  → Build YouTube API service
  → Create MediaFileUpload (resumable, 4MB chunks)
  → videos().insert(part="snippet,status")
  → Upload progress tracked chunk-by-chunk
  → If thumbnail available:
      → thumbnails().set(videoId, media)
  → Update DB: status=UPLOADED, youtube_id, uploaded_at
  → Transition topic to UPLOADED state
```

## File Layout

```
data/
├── youtube_token.json        # OAuth2 credentials (persisted)
└── projects/
    └── {topic_id}/
        └── video/
            ├── documentary-mvp.mp4
            └── thumbnail.jpg
```
