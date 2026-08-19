"""tracksnap state — SQLite persistence for seen item tracking."""
from __future__ import annotations

import os
import pathlib
import sqlite3
from datetime import datetime, timezone

DB_PATH_ENV = "TRACKSNAP_DB"


def get_db_path() -> pathlib.Path:
    """Return path to the state DB (override with TRACKSNAP_DB env var)."""
    if env := os.environ.get(DB_PATH_ENV):
        return pathlib.Path(env)
    data_dir = pathlib.Path.home() / ".local" / "share" / "tracksnap"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "state.db"


def get_conn(db_path=None) -> sqlite3.Connection:
    """Open (or create) the state DB and ensure the schema exists."""
    path = pathlib.Path(db_path) if db_path else get_db_path()
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_items (
            feed_url   TEXT NOT NULL,
            item_id    TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            PRIMARY KEY (feed_url, item_id)
        )
    """)
    conn.commit()
    return conn


def get_seen_ids(conn: sqlite3.Connection, feed_url: str) -> set:
    """Return the set of item IDs already seen for feed_url."""
    cur = conn.execute(
        "SELECT item_id FROM seen_items WHERE feed_url=?", (feed_url,)
    )
    return {row[0] for row in cur.fetchall()}


def mark_seen(conn: sqlite3.Connection, feed_url: str, item_ids: list) -> None:
    """Record item_ids as seen for feed_url (idempotent)."""
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "INSERT OR IGNORE INTO seen_items(feed_url, item_id, first_seen) VALUES(?,?,?)",
        [(feed_url, iid, now) for iid in item_ids],
    )
    conn.commit()


def reset_feed(conn: sqlite3.Connection, feed_url: str) -> None:
    """Delete all seen records for feed_url."""
    conn.execute("DELETE FROM seen_items WHERE feed_url=?", (feed_url,))
    conn.commit()
