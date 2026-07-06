# Phase 4: YouTube Integration — Code Examples

## 1. YouTube Authentication

```python
from backend.youtube.auth import get_auth_url, exchange_code, is_authenticated

# Get the OAuth URL
url = get_auth_url()
print(f"Open this URL: {url}")

# After user grants consent and pastes the code
credentials = exchange_code("4/0AeaYSHB...")
print("Authenticated!")

# Check if authenticated
if is_authenticated():
    print("Token is valid")
```

## 2. Upload a Video to YouTube

```python
from backend.youtube.uploader import upload_video

result = upload_video(
    video_path="data/projects/.../video/documentary-mvp.mp4",
    title="The Great Molasses Flood of 1919",
    description="An AI-assisted documentary about the Boston Molasses Flood.",
    tags=["documentary", "history", "education"],
    thumbnail_path="data/projects/.../video/thumbnail.jpg",
)

print(f"YouTube ID: {result['youtube_id']}")
print(f"URL: {result['youtube_url']}")
```

## 3. Full CLI Workflow

```bash
# 1. Check auth status
curl http://localhost:8000/api/publish/auth/status

# 2. Get OAuth URL
curl http://localhost:8000/api/publish/auth/url

# 3. Exchange auth code
curl -X POST http://localhost:8000/api/publish/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "4/0AeaYSHB..."}'

# 4. Build metadata
curl -X POST http://localhost:8000/api/publish/metadata \
  -H "Content-Type: application/json" \
  -d '{"video_id": "your-video-uuid"}'

# 5. Approve
curl -X POST http://localhost:8000/api/publish/{upload_id}/approve

# 6. Upload to YouTube
curl -X POST http://localhost:8000/api/publish/{upload_id}/upload-to-youtube
```

## 4. Python Upload with Progress Monitoring

```python
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from backend.youtube.auth import load_credentials

creds = load_credentials()
youtube = build("youtube", "v3", credentials=creds)

media = MediaFileUpload("video.mp4", chunksize=4*1024*1024, resumable=True)
request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {"title": "My Doc", "description": "...", "tags": ["doc"], "categoryId": "27"},
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
    },
    media_body=media,
)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"Progress: {int(status.progress() * 100)}%")
```
