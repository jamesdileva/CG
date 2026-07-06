# Phase 4: YouTube Integration — Lessons Learned

## Design Decisions

### 1. OAuth Desktop Flow with Code Exchange
- YouTube Data API requires OAuth 2.0 — no API-key-only upload
- Used `google_auth_oauthlib.InstalledAppFlow` for the desktop app flow
- Token persisted to `data/youtube_token.json` so auth persists across restarts
- Redirect URI `http://localhost` with manual code copy (simpler than running a local HTTP server)

### 2. Resumable Upload (4MB Chunks)
- YouTube API supports resumable uploads, which are more reliable for large files
- Progress tracking at the chunk level provides feedback during long uploads
- `MediaFileUpload` with `chunksize=4*1024*1024` and `resumable=True`

### 3. Thumbnail Auto-Upload
- Phase 3 generates thumbnails as assets
- Uploader auto-selects the most recent thumbnail asset for the topic
- No UI selection needed (decision made in planning)

### 4. Privacy Set to Unlisted
- Unlisted videos are accessible via link but don't appear in search results
- Safe for testing while still being usable
- Can be changed to public later in the YouTube Studio UI

### 5. Mock Upload Preserved
- The mock-upload endpoint is kept alongside the real upload for testing
- Useful for development without YouTube credentials
- Simulates the same state transitions

## Gotchas

### Token Expiry
- OAuth tokens expire after 7 days without use
- The refresh token persists indefinitely (unless revoked)
- `google-auth` library handles auto-refresh when building the service

### API Quotas
- YouTube Data API has daily quotas (typically 10,000 units/day)
- Each upload costs ~1,600 units (resumable upload)
- Don't upload excessively during development

### Redirect URI Matching
- The redirect URI must exactly match what's registered in Google Cloud Console
- Our flow uses manual code copy, so `http://localhost` as redirect is sufficient
- No local server needed for the callback

### File Size Limits
- YouTube accepts videos up to 256GB or 12 hours
- Resumable upload handles files of any size within those limits
- 4MB chunks keep memory usage low

## Future Improvements

- Upload scheduling (set `scheduled_at` for delayed publishing)
- Multiple channel support
- Upload playlist management
- Real-time upload progress in the frontend
- YouTube Data API quota monitoring
