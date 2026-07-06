# Phase 4: YouTube Integration — Overview

## Goal

Upload rendered documentary videos to YouTube with metadata (title, description, tags) and thumbnails, using proper OAuth2 authentication.

## What Was Built

### Backend

| Module | File | Purpose |
|---|---|---|
| YouTube Auth | `backend/youtube/auth.py` | OAuth 2.0 desktop flow, token storage |
| YouTube Uploader | `backend/youtube/uploader.py` | Resumable video upload + thumbnail via Data API v3 |
| Publish API | `backend/api/publish.py` | Auth endpoints, real upload replacing mock |

### Frontend

| Page | Updates |
|---|---|
| Publish (`Publish.tsx`) | YouTube Sign-In, code exchange, real upload button, upload result display |

---

## Workflow

```
User clicks "Sign in"
       ↓
Opens Google OAuth URL in browser
       ↓
Grants permissions → receives auth code
       ↓
Pastes code → POST /auth/callback
       ↓
Token saved to data/youtube_token.json
       ↓
User clicks "Build Metadata"
       ↓
User clicks "Approve"
       ↓
User clicks "Upload to YouTube"
       ↓
Backend: resumable upload (4MB chunks)
       ↓
Backend: upload thumbnail (if available)
       ↓
YouTube ID returned → DB updated → state = UPLOADED
```

## Key Decisions

- **OAuth**: Desktop app flow with `google_auth_oauthlib`, token persisted to disk
- **Privacy**: Unlisted (anyone with link can view, not searchable)
- **Thumbnail**: Auto-uploads the first thumbnail asset from Phase 3
- **Upload**: Resumable (4MB chunks) via YouTube Data API v3
- **Category**: Education (category ID 27)
