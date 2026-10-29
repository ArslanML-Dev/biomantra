# Scoring rules: points, weekly window, hotspots

Source: `backend/app/scoring.py` (39 lines in total), copied unchanged.

Lines 7–10:

```python
POINTS = {"sapling": 4, "segregated_bin": 2, "cleanup": 5, "dumping_report": 2}
SAPLING_NOTE = "+3 at 30 days, +3 at 90 days: pending re-check"
WEEKLY_GOAL = 50
HOTSPOT_CLOSE_KM = 0.150
```

Lines 19–53:

```python
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
```
