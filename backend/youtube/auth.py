from __future__ import annotations

import json
import secrets
from pathlib import Path

from google.auth.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from backend.core.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
TOKEN_PATH = Path(settings.youtube_token_path)

_code_verifier: str | None = None


def _client_config() -> dict:
    return {
        "installed": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def is_authenticated() -> bool:
    if not TOKEN_PATH.exists():
        return False
    try:
        creds = load_credentials()
        if creds is None:
            return False
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            save_credentials(creds)
        return creds.valid
    except Exception:
        return False


def load_credentials() -> Credentials | None:
    if not TOKEN_PATH.exists():
        return None
    from google.oauth2.credentials import Credentials as OAuthCredentials
    data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    return OAuthCredentials.from_authorized_user_info(data, SCOPES)


def save_credentials(credentials: Credentials) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    TOKEN_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_auth_url() -> str:
    global _code_verifier
    _code_verifier = secrets.token_urlsafe(64)

    flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
    flow.redirect_uri = "http://localhost"
    flow.code_verifier = _code_verifier
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge_method="S256",
    )
    return auth_url


def exchange_code(authorization_code: str) -> Credentials:
    global _code_verifier
    flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
    flow.redirect_uri = "http://localhost"
    flow.code_verifier = _code_verifier
    _code_verifier = None
    flow.fetch_token(code=authorization_code)
    save_credentials(flow.credentials)
    return flow.credentials
