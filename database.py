"""SQLite conversation memory + message dedup.

One table holds every message. A second table records which Green API
message IDs we've already handled, so a Render restart (which replays the
last webhook) does not answer the same message twice.

Connection is opened per call - simplest correct choice at Render scale.
"""
import sqlite3
from contextlib import contextmanager

from config import DATABASE_PATH, MAX_HISTORY


@contextmanager
def _conn():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id    TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_chat ON conversations(chat_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_messages (
                id_message TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def append(chat_id: str, role: str, content: str) -> None:
    """Store one message. role is 'user' or 'assistant'."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO conversations (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )


def tail(chat_id: str, n: int = MAX_HISTORY):
    """Return the last n messages for a chat, oldest first."""
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM conversations
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, n),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def already_processed(id_message: str) -> bool:
    """True if this Green API message ID was handled before."""
    if not id_message:
        return False
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_messages WHERE id_message = ?",
            (id_message,),
        ).fetchone()
    return row is not None


def mark_processed(id_message: str) -> None:
    if not id_message:
        return
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_messages (id_message) VALUES (?)",
            (id_message,),
        )
