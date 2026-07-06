"""SQLite database initialization and connection management"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "studio.db"
SCHEMA_PATH = Path(__file__).parent.parent.parent / "database" / "schema.sql"


def init_db():
    """Initialize database and create schema if needed"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    try:
        schema = SCHEMA_PATH.read_text()
        cursor.executescript(schema)
        _ensure_column(cursor, "jobs", "updated_at", "TIMESTAMP")
        _ensure_column(cursor, "youtube_uploads", "tags", "TEXT")
        _ensure_column(cursor, "youtube_uploads", "created_at", "TIMESTAMP")
        _ensure_column(cursor, "analytics", "topic_score", "REAL DEFAULT 0.0")
        _ensure_column(cursor, "topics", "interest_score", "REAL DEFAULT 0.0")
        _ensure_column(cursor, "topics", "uniqueness_score", "REAL DEFAULT 0.0")
        _ensure_column(cursor, "topics", "source_score", "REAL DEFAULT 0.0")
        _ensure_column(cursor, "topics", "category", "TEXT DEFAULT 'General'")
        _ensure_column(cursor, "assets", "caption", "TEXT")
        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_column(cursor: sqlite3.Cursor, table: str, column: str, column_type: str) -> None:
    """Add a column for existing SQLite databases when schema evolves."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column not in existing_columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


@contextmanager
def get_db():
    """Get database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()):
    """Execute a query and return results"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_update(query: str, params: tuple = ()):
    """Execute an update query"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
