"""SQLite database: schema, seed data and a connection helper (SPEC §6)."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("BIOMANTRA_DB", BACKEND_DIR / "biomantra.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS institutions (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  institution_id INTEGER REFERENCES institutions(id));
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  action_type TEXT NOT NULL CHECK (action_type IN ('sapling','segregated_bin','cleanup','dumping_report')),
  photo_path TEXT NOT NULL, before_photo_path TEXT,
  lat REAL NOT NULL, lon REAL NOT NULL,
  client_time TEXT NOT NULL, server_time TEXT NOT NULL,
  phash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('approved','needs_review','rejected')),
  reasons TEXT NOT NULL,
  confidence REAL, detections TEXT,
  model_version TEXT, points INTEGER DEFAULT 0,
  reviewed_by TEXT, reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS hotspots (
  id INTEGER PRIMARY KEY, action_id INTEGER REFERENCES actions(id),
  lat REAL, lon REAL, created_at TEXT, cleaned_action_id INTEGER, cleaned_at TEXT
);
"""

SEED = {
    "CSE-DS": ["Aarav Sharma", "Diya Patel"],
    "CSE-AI": ["Kabir Singh", "Ananya Gupta"],
    "CSE-AIML": ["Vihaan Verma", "Isha Reddy"],
    "CSE-IT": ["Arjun Mehta", "Sara Khan"],
    "ECE": ["Rohan Das", "Meera Iyer"],
}


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Open a connection with dict-like rows; commit on success and always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the tables and seed institutions/users if the database is empty."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]:
            return
        for inst, users in SEED.items():
            inst_id = conn.execute("INSERT INTO institutions (name) VALUES (?)", (inst,)).lastrowid
            conn.executemany("INSERT INTO users (name, institution_id) VALUES (?, ?)",
                             [(u, inst_id) for u in users])
