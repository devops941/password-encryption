import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "vault.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS master (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    salt BLOB NOT NULL,
    check_token BLOB NOT NULL,
    iterations INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS vault (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    username TEXT,
    password_enc BLOB NOT NULL,
    notes_enc BLOB,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    return conn


def is_initialized(conn: sqlite3.Connection) -> bool:
    cur = conn.execute("SELECT 1 FROM master WHERE id = 1")
    return cur.fetchone() is not None


def save_master_record(conn: sqlite3.Connection, salt: bytes, check_token: bytes, iterations: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO master (id, salt, check_token, iterations) VALUES (1, ?, ?, ?)",
        (salt, check_token, iterations),
    )
    conn.commit()


def load_master_record(conn: sqlite3.Connection):
    cur = conn.execute("SELECT salt, check_token, iterations FROM master WHERE id = 1")
    return cur.fetchone()


def add_entry(conn: sqlite3.Connection, site: str, username: str, password_enc: bytes, notes_enc: bytes) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO vault (site, username, password_enc, notes_enc, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (site, username, password_enc, notes_enc, now, now),
    )
    conn.commit()
    return cur.lastrowid


def update_entry(conn: sqlite3.Connection, entry_id: int, site: str, username: str, password_enc: bytes, notes_enc: bytes) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE vault SET site = ?, username = ?, password_enc = ?, notes_enc = ?, updated_at = ? "
        "WHERE entry_id = ?",
        (site, username, password_enc, notes_enc, now, entry_id),
    )
    conn.commit()


def delete_entry(conn: sqlite3.Connection, entry_id: int) -> None:
    conn.execute("DELETE FROM vault WHERE entry_id = ?", (entry_id,))
    conn.commit()


def get_all_entries(conn: sqlite3.Connection):
    cur = conn.execute(
        "SELECT entry_id, site, username, password_enc, notes_enc, created_at, updated_at "
        "FROM vault ORDER BY site COLLATE NOCASE"
    )
    return cur.fetchall()


def search_entries(conn: sqlite3.Connection, query: str):
    like = f"%{query}%"
    cur = conn.execute(
        "SELECT entry_id, site, username, password_enc, notes_enc, created_at, updated_at "
        "FROM vault WHERE site LIKE ? OR username LIKE ? ORDER BY site COLLATE NOCASE",
        (like, like),
    )
    return cur.fetchall()
