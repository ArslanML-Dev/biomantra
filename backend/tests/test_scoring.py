"""Tests for points, the weekly window and hotspot closing (SPEC §12)."""
from datetime import datetime, timezone

import pytest

from app import scoring
from app.db import get_conn


def add_action(action_type: str, lat: float = 28.4725, lon: float = 77.4889,
               when: str = "2026-10-28T09:00:00+00:00", user_id: int = 1) -> int:
    """Insert an approved action row and apply its points; return its id."""
    with get_conn() as conn:
        action_id = conn.execute("""
            INSERT INTO actions (user_id, action_type, photo_path, lat, lon, client_time,
              server_time, phash, status, reasons)
            VALUES (?, ?, 'x.jpg', ?, ?, ?, ?, 'ff', 'approved', '[]')""",
            (user_id, action_type, lat, lon, when, when)).lastrowid
        scoring.apply_approval(conn, action_id)
    return action_id


@pytest.mark.parametrize("action_type, points", [
    ("sapling", 4), ("segregated_bin", 2), ("cleanup", 5), ("dumping_report", 2)])
def test_points_by_type(fresh_db, action_type: str, points: int) -> None:
    """Each approved action type gets its fixed points."""
    action_id = add_action(action_type)
    with get_conn() as conn:
        assert conn.execute("SELECT points FROM actions WHERE id = ?", (action_id,)).fetchone()[0] == points


def test_week_starts_monday_midnight_ist() -> None:
    """Sunday 23:59 IST is last week; Monday 00:00 IST starts a new week."""
    # 2026-10-26 is a Monday. Monday 00:00 IST = Sunday 18:30 UTC.
    monday = datetime(2026, 10, 25, 18, 30, tzinfo=timezone.utc)
    assert scoring.week_start(datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)) == monday
    sunday_late = datetime(2026, 10, 25, 18, 29, tzinfo=timezone.utc)  # Sun 23:59 IST
    assert scoring.week_start(sunday_late) < monday


def test_leaderboard_weekly_points(fresh_db) -> None:
    """Only this week's points count toward points_week; all count toward the total."""
    add_action("sapling", when="2026-10-27T09:00:00+00:00")        # this week
    add_action("segregated_bin", when="2026-10-20T09:00:00+00:00")  # last week
    with get_conn() as conn:
        board = scoring.leaderboard(conn, "institutions", datetime(2026, 10, 28, tzinfo=timezone.utc))
    top = board[0]
    assert (top["name"], top["points_week"], top["points_total"]) == ("CSE-DS", 4, 6)
    assert top["progress"] == round(4 / 50, 3)
    assert len(board) == 5


def test_cleanup_within_150m_closes_hotspot(fresh_db) -> None:
    """A cleanup ~100 m away closes the hotspot; one ~500 m away does not."""
    add_action("dumping_report", lat=28.4725, lon=77.4889)
    add_action("cleanup", lat=28.4770, lon=77.4889)  # ~500 m north
    with get_conn() as conn:
        assert conn.execute("SELECT cleaned_action_id FROM hotspots").fetchone()[0] is None
    cleanup_id = add_action("cleanup", lat=28.4734, lon=77.4889)  # ~100 m north
    with get_conn() as conn:
        assert conn.execute("SELECT cleaned_action_id FROM hotspots").fetchone()[0] == cleanup_id
