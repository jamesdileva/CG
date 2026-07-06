# Phase 4: YouTube Integration — API Reference

All endpoints under `/api/publish`

---

## Authentication

### `GET /api/publish/auth/status`

Check if YouTube OAuth token exists and is valid.

**Response:**
```json
{ "authenticated": true }
```

### `GET /api/publish/auth/url`

Get the Google OAuth consent URL.

**Response:**
```json
{ "auth_url": "https://accounts.google.com/o/oauth2/auth?..." }
```

### `POST /api/publish/auth/callback`

Exchange an OAuth authorization code for credentials.

**Body:**
```json
{ "code": "4/0AeaYSHB..." }
```

**Response:**
```json
{ "message": "Authentication successful" }
```

---

## Upload

### `POST /api/publish/{upload_id}/upload-to-youtube`

Upload the video to YouTube with metadata and thumbnail.

**Response:**
```json
{
  "message": "Upload to YouTube complete",
  "upload_id": "uuid",
  "youtube_id": "dQw4w9WgXcQ",
  "youtube_url": "https://youtu.be/dQw4w9WgXcQ",
  "title": "My Documentary"
}
```

### `POST /api/publish/{upload_id}/mock-upload`

Simulate an upload for local testing (no YouTube API call).

**Response:**
```json
{
  "message": "Mock upload complete",
  "upload_id": "uuid",
  "youtube_id": "local-abc12345"
}
```

---

## Existing Endpoints (Phase 1 scaffold)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/publish/metadata` | Build publish metadata |
| GET | `/api/publish` | List uploads (optional ?status=) |
| GET | `/api/publish/{upload_id}` | Get single upload record |
| POST | `/api/publish/{upload_id}/update` | Update metadata |
| POST | `/api/publish/{upload_id}/approve` | Mark ready to upload |
