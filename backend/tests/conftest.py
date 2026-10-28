"""Shared test fixtures: a fresh temporary database and uploads folder for every test."""
from pathlib import Path

import pytest

from app import db


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the app at an empty, seeded SQLite file in a temp folder."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return tmp_path
