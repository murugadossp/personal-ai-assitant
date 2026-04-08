import os
import sqlite3

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
DB_FILE = os.path.join(_PROJECT_ROOT, "agent_system.db")
_CONNECT_TIMEOUT_S = 30.0


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_FILE, timeout=_CONNECT_TIMEOUT_S)


def init_db():
    """Initializes the SQLite database correctly tracking sessions and message history."""
    conn = _connect()
    cursor = conn.cursor()
    # Table to track unique conversation sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            user_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Table to track messages from the user, assistant (ADK) and tools (MCP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def ensure_conversation(session_id: str, user_id: str | None = None) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO conversations (session_id, user_id)
            VALUES (?, ?)
            """,
            (session_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def append_message(session_id: str, role: str, content: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content)
            VALUES (?, ?, ?)
            """,
            (session_id, role, content),
        )
        conn.commit()
    finally:
        conn.close()
