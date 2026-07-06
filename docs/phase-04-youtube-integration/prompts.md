# Phase 4: YouTube Integration — Prompts & Templates

## YouTube Metadata Defaults

### Title
Auto-generated from topic title (truncated to 90 characters).

### Description
```
{topic_description or topic_title}

Generated with AI Documentary Studio. Review sources and script before publishing.
```

### Default Tags
```
documentary, history, education, longform
```

### YouTube Category
- **ID**: `27` (Education)

### Privacy Status
- **Value**: `unlisted` (anyone with link can view, not searchable)

## OAuth Scopes

```
https://www.googleapis.com/auth/youtube.upload
```

This scope only allows uploading videos — no channel management, analytics, or other access.

## Environment Variables

```env
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_TOKEN_PATH=data/youtube_token.json
```

## Setting Up Google Cloud Credentials

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials:
   - Application type: **Desktop app**
   - Name: "AI Documentary Studio"
5. Download JSON → copy `client_id` and `client_secret` to `.env`
6. Add `http://localhost` to **Authorized redirect URIs**

## OAuth Flow Notes

- The token is saved to `data/youtube_token.json`
- Refresh tokens are included, so re-authentication is not needed until token expires or is revoked
- If the token file is deleted, the user must re-authenticate
- The flow uses `http://localhost` as redirect URI — the user copies the code from the browser after granting consent
