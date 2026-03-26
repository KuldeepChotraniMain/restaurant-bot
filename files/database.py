"""
database.py — SQLite connection helpers (Flask g-based per-request pooling)
"""

import sqlite3
from flask import g
from config import Config


def get_db() -> sqlite3.Connection:
    """Return (or create) the per-request SQLite connection stored on Flask g."""
    if "db" not in g:
        g.db = sqlite3.connect(Config.DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None) -> None:
    """Teardown — called automatically by Flask after each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def raw_connection() -> sqlite3.Connection:
    """
    Open a *fresh* connection outside of a request context.
    Callers are responsible for committing and closing.
    Used exclusively during app initialisation / seeding.
    """
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
