# Demo rehearsal (API level, 2026-10-29)

Two runs, each from a fresh start: backend stopped, `biomantra.db` and uploads deleted, uvicorn restarted.

| Step | Run 1 | Run 2 |
|---|---|---|
| GET /forecast | 200, "Poor" | 200, "Poor" |
| GET /leaderboard (before) | all points_total 0 | all points_total 0 |
| POST /actions (COCO plant as sapling, user 1) | needs_review | needs_review |
| POST /admin/review/1 approve | approved, +4 | approved, +4 |
| GET /leaderboard (after) | CSE-DS points_total 4, points_week 4 | same |
| GET /hotspots | [] | [] |
| Tracebacks/ERROR lines in server log | 0 | 0 |

Not rehearsed automatically (WAITING FOR USER): the visual flow on the projector (website /map and /leaderboard), and the action from the phone app.
