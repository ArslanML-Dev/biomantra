# D1-T10 live API check (real YOLOv8n, local server, 2026-10-28)

1. `curl -F user_id=1 -F action_type=sapling -F lat=28.4725 -F lon=77.4889 -F client_time=<now> -F photo=@coco_139_plant.jpg /actions`
   → `{"id":1,"status":"needs_review","confidence":0.421,"points":0,"reasons":["AI is not fully sure — sent to a coordinator"], ...13 detections}`
2. Same photo again (user 2) → `{"id":2,"status":"rejected","confidence":null,"reasons":["this photo (or a near copy) was already submitted"]}`
3. `GET /leaderboard?scope=institutions` → all 5 institutions at 0 points (nothing approved yet).
4. `POST /admin/review/1 {"decision":"approve","reviewer":"demo"}` with `X-Admin-Token` → `{"id":1,"status":"approved","points":4}`
5. `GET /leaderboard?scope=users` → rank 1 Aarav Sharma, points_total 4, points_week 4, progress 0.08.
6. `GET /uploads/<uuid>.jpg` → 200 image/jpeg.

`pytest -q` → 30 passed (test_dataset, test_forecast, test_verify, test_scoring, test_api).
