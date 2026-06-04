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
    cursor = conn.cursor()

    try:
        schema = SCHEMA_PATH.read_text()
        cursor.executescript(schema)
        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_db():
    """Get database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
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
