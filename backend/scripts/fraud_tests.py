"""Run the SPEC §12 manual fraud cases against a running backend and print a markdown table.

Usage (from backend/, server running, ideally on a fresh database):
    python scripts/fraud_tests.py --plant plant.jpg --wall wall.jpg [--screen screen.jpg]
        [--before littered.jpg --after-clean clean.jpg --after-dirty still_littered.jpg]
        [--url http://localhost:8000]
Cases whose photos are not given are listed as "not run".
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402


def submit(url: str, action_type: str, photo: str, before: str | None = None,
           lat: float = settings.LAT, lon: float = settings.LON, age_min: float = 0) -> dict:
    """POST one action like the app does; return the JSON response."""
    client_time = (datetime.now(timezone.utc) - timedelta(minutes=age_min)).isoformat()
    files = {"photo": open(photo, "rb")}
    if before:
        files["before_photo"] = open(before, "rb")
    resp = requests.post(f"{url}/actions", files=files, timeout=120, data={
        "user_id": 1, "action_type": action_type, "lat": lat, "lon": lon, "client_time": client_time})
    return resp.json() if resp.ok else {"status": f"HTTP {resp.status_code}", "reasons": [resp.text]}


def main() -> None:
    """Run every case that has its photos and print the result table."""
    p = argparse.ArgumentParser()
    for name in ("plant", "wall", "screen", "before", "after-clean", "after-dirty"):
        p.add_argument(f"--{name}")
    p.add_argument("--url", default="http://localhost:8000")
    a = p.parse_args()
    # Case 8 runs before 4/5 because those reuse the wall photo (its hash is stored even when rejected).
    cases = [
        (1, "Live photo of a potted plant", "approved or needs_review",
         a.plant and (lambda: submit(a.url, "sapling", a.plant))),
        (2, "Same photo submitted again", "rejected (duplicate)",
         a.plant and (lambda: submit(a.url, "sapling", a.plant))),
        (3, "Photo of a screen showing a plant image", "record the honest result",
         a.screen and (lambda: submit(a.url, "sapling", a.screen))),
        (8, "Random photo (wall) as sapling", "rejected",
         a.wall and (lambda: submit(a.url, "sapling", a.wall))),
        (4, "Far location (Mumbai coordinates)", "rejected (geofence)",
         a.wall and (lambda: submit(a.url, "sapling", a.wall, lat=19.076, lon=72.877))),
        (5, "client_time 2 h old", "rejected (clock)",
         a.wall and (lambda: submit(a.url, "sapling", a.wall, age_min=120))),
        (6, "Cleanup: littered before, clean after", "approved / needs_review",
         a.before and a.after_clean and (lambda: submit(a.url, "cleanup", a.after_clean, a.before))),
        (7, "Cleanup: after still littered", "rejected",
         a.before and a.after_dirty and (lambda: submit(a.url, "cleanup", a.after_dirty, a.before))),
    ]
    rows = []
    for num, case, expected, run in cases:
        if not run:
            rows.append((num, f"| {num} | {case} | {expected} | not run (photo missing) | | |"))
            continue
        r = run()
        rows.append((num, f"| {num} | {case} | {expected} | {r['status']} | {r.get('confidence')} | "
                          f"{'; '.join(r['reasons'])} |"))
    print("| # | Case | Expected | Actual status | Confidence | Reasons |")
    print("|---|---|---|---|---|---|")
    for _, row in sorted(rows):
        print(row)


if __name__ == "__main__":
    main()
