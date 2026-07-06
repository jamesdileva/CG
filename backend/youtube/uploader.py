from __future__ import annotations

import json
import logging
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from backend.youtube.auth import load_credentials, is_authenticated

logger = logging.getLogger(__name__)

_PRIVACY_STATUS = "public"
_CATEGORY_ID = "27"  # Education


def _get_service():
    creds = load_credentials()
    if not creds:
        raise RuntimeError("YouTube authentication required. Run auth flow first.")
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    if not creds.valid:
        raise RuntimeError("YouTube authentication required. Run auth flow first.")
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    thumbnail_path: str | None = None,
) -> dict:
    if not is_authenticated():
        raise RuntimeError("YouTube authentication required. Run auth flow first.")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    youtube = _get_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:30],
            "categoryId": _CATEGORY_ID,
        },
        "status": {
            "privacyStatus": _PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path_obj), chunksize=4 * 1024 * 1024, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    logger.info("Starting YouTube upload (resumable)...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info("Upload progress: %d%%", int(status.progress() * 100))

    youtube_id = response.get("id", "")
    logger.info("Upload complete. YouTube ID: %s", youtube_id)

    if thumbnail_path and youtube_id:
        _upload_thumbnail(youtube, youtube_id, thumbnail_path)

    return {
        "youtube_id": youtube_id,
        "youtube_url": f"https://youtu.be/{youtube_id}",
        "title": title,
    }


def _upload_thumbnail(youtube, video_id: str, thumbnail_path: str) -> None:
    thumb_path = Path(thumbnail_path)
    if not thumb_path.exists():
        logger.warning("Thumbnail not found: %s", thumbnail_path)
        return

    media = MediaFileUpload(str(thumb_path))
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=media,
    ).execute()
    logger.info("Thumbnail uploaded for video %s", video_id)
