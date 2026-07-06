"""Pytest fixtures for backend tests."""
import pytest
import tempfile
import os
import sqlite3
from pathlib import Path
from backend.core.database import get_db
from unittest.mock import AsyncMock


@pytest.fixture(autouse=True)
def test_db(tmp_path):
    """Use a temporary SQLite database for each test."""
    from backend.core import database as db_module

    original_path = db_module.DB_PATH
    test_path = tmp_path / "test.db"
    db_module.DB_PATH = test_path

    db_module.init_db()

    yield get_db

    db_module.DB_PATH = original_path
    if test_path.exists():
        test_path.unlink()


@pytest.fixture
def db_conn(test_db):
    """Get a database connection for the test."""
    with test_db() as conn:
        yield conn


@pytest.fixture
def sample_topic(db_conn):
    """Insert a sample topic and return its id."""
    import uuid
    topic_id = str(uuid.uuid4())
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    db_conn.execute(
        "INSERT INTO topics (id, title, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (topic_id, "The Great Molasses Flood of 1919", "A historical event in Boston", "APPROVED", now, now),
    )
    db_conn.commit()
    return topic_id


@pytest.fixture
def mock_httpx(monkeypatch):
    """Mock httpx to avoid real network calls."""
    import httpx

    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
        <h1>Test Article</h1>
        <p>The Great Molasses Flood of 1919 occurred in Boston on January 15, 1919.
        It was caused by a massive storage tank failure. The flood killed 21 people
        and injured 150. The tank had been poorly constructed and tested.</p>
        </body></html>
        """
        mock_response.url = str(args[0]) if args else "http://example.com"
        mock_response.raise_for_status = lambda: None
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    return mock_get


@pytest.fixture
def mock_failed_httpx(monkeypatch):
    """Mock httpx to simulate network failure."""
    import httpx

    async def mock_failed_get(*args, **kwargs):
        raise httpx.RequestError("Connection failed")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_failed_get)
    return mock_failed_get
