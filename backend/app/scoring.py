"""Points, hotspots, weekly goals and the leaderboard (SPEC §8)."""
import sqlite3
from datetime import datetime, timedelta, timezone

from app.verify import haversine_km

POINTS = {"sapling": 4, "segregated_bin": 2, "cleanup": 5, "dumping_report": 2}
SAPLING_NOTE = "+3 at 30 days, +3 at 90 days: pending re-check"
WEEKLY_GOAL = 50
HOTSPOT_CLOSE_KM = 0.150
IST = timezone(timedelta(hours=5, minutes=30))


def now_iso() -> str:
    """Current UTC time as an ISO string (the format stored in the database)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def week_start(now: datetime) -> datetime:
    """Monday 00:00 IST of the week containing `now`, returned in UTC."""
    local = now.astimezone(IST)
    monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0,
                                                               microsecond=0)
    return monday.astimezone(timezone.utc)


def close_nearest_hotspot(conn: sqlite3.Connection, action_id: int, lat: float, lon: float,
                          when: str) -> int | None:
    """Close the nearest open hotspot within 150 m of a cleanup; return its id."""
    open_spots = conn.execute(
        "SELECT id, lat, lon FROM hotspots WHERE cleaned_action_id IS NULL").fetchall()
    near = [(haversine_km(lat, lon, s["lat"], s["lon"]), s["id"]) for s in open_spots]
    near = [n for n in near if n[0] <= HOTSPOT_CLOSE_KM]
    if not near:
        return None
    spot_id = min(near)[1]
    conn.execute("UPDATE hotspots SET cleaned_action_id = ?, cleaned_at = ? WHERE id = ?",
                 (action_id, when, spot_id))
    return spot_id


def apply_approval(conn: sqlite3.Connection, action_id: int) -> int:
    """Give points for an approved action and update hotspots; return the points."""
    action = conn.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
    points = POINTS[action["action_type"]]
    when = action["reviewed_at"] or action["server_time"]
    conn.execute("UPDATE actions SET points = ? WHERE id = ?", (points, action_id))
    if action["action_type"] == "dumping_report":
        conn.execute("INSERT INTO hotspots (action_id, lat, lon, created_at) VALUES (?, ?, ?, ?)",
                     (action_id, action["lat"], action["lon"], when))
    if action["action_type"] == "cleanup":
        close_nearest_hotspot(conn, action_id, action["lat"], action["lon"], when)
    return points


def leaderboard(conn: sqlite3.Connection, scope: str, now: datetime) -> list[dict]:
    """Ranked users or institutions with total points, this week's points and goal progress."""
    since = week_start(now).isoformat(timespec="seconds")
    t = "u" if scope == "users" else "i"  # table alias to group by (fixed values, not user input)
    rows = conn.execute(f"""
        SELECT {t}.id AS id, {t}.name AS name,
               COALESCE(SUM(a.points), 0) AS points_total,
               COALESCE(SUM(CASE WHEN COALESCE(a.reviewed_at, a.server_time) >= ?
                                 THEN a.points END), 0) AS points_week
        FROM institutions i
        JOIN users u ON u.institution_id = i.id
        LEFT JOIN actions a ON a.user_id = u.id AND a.status = 'approved'
        GROUP BY {t}.id
        ORDER BY points_week DESC, points_total DESC, name""", (since,)).fetchall()
    return [{"rank": rank, **dict(r), "goal": WEEKLY_GOAL,
             "progress": round(min(1.0, r["points_week"] / WEEKLY_GOAL), 3)}
            for rank, r in enumerate(rows, 1)]
