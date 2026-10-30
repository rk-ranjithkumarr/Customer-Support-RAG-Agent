import sqlite3
from datetime import datetime, timezone
from . import config


def _conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, session_id TEXT,
        email TEXT, summary TEXT, transcript TEXT, status TEXT DEFAULT 'open')""")
    return c


def create_ticket(session_id: str, email: str, summary: str, transcript: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO tickets(created_at,session_id,email,summary,transcript) VALUES(?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), session_id, email, summary, transcript))
        return cur.lastrowid


def list_tickets(limit: int = 50) -> list[dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,))]
