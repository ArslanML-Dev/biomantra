# API reference (FastAPI, `backend/app/main.py`)

- **Base URL:** `http://<laptop-IP>:8000` (demo) or `http://localhost:8000`.
- **Format:** JSON, except `POST /actions` (multipart form data) and `/uploads/*` (images).
- **CORS:** every origin is allowed. No cookies are used; the admin pages use a header token.
- **Samples:** every one below is a **real response**, copied from `raw/api_check.txt` (`start_demo.ps1 -Fresh`, 2026-10-29 13:40 UTC) or `raw/api_check_actions.txt` (throwaway database, real YOLOv8n, 2026-10-29 13:58 UTC). Long responses are cut where marked "…".

| # | Method | Path | Auth | Purpose |
|---|---|---|---|---|
| 1 | GET | `/health` | – | liveness check |
| 2 | GET | `/forecast` | – | tomorrow's PM2.5 (next-24 h mean), CPCB category, SHAP reason, tip |
| 3 | GET | `/meta` | – | users, institutions and model metrics (user picker, About page) |
| 4 | POST | `/actions` | – | submit an eco-action photo; runs the fraud gate and YOLO |
| 5 | GET | `/leaderboard` | – | ranked users or institutions with weekly goal progress |
| 6 | GET | `/hotspots` | – | dumping hotspots (open or cleaned) |
| 7 | GET | `/admin/review` | `X-Admin-Token` | queue of `needs_review` actions |
| 8 | POST | `/admin/review/{id}` | `X-Admin-Token` | approve or reject one queued action |
| 9 | GET | `/uploads/{file}` | – | stored photo (static files) |

---

## 1. GET /health
No inputs.
```json
{"ok":true}
```

## 2. GET /forecast
| Query | Type | Default | Notes |
|---|---|---|---|
| `lat`, `lon` | float | campus LAT/LON from `.env` | location |
| `lang` | `en` \| `hi` | `en` | language of `reason`, `tip`, `disclaimer` |

The result is cached for 30 minutes per location (rounded to 2 decimals). If Open-Meteo can't be reached, the endpoint returns HTTP 503.

`?lang=en`:
```json
{"location":{"lat":28.4725,"lon":77.4889},"generated_at":"2026-10-29T13:40:27Z","pm25_now":46.3,"pm25_tomorrow":55.2,"category":"Satisfactory","tier":1,"color":"#92D050","reason":"Tomorrow looks Satisfactory mainly because recent rain has cleaned the air and rain is forecast.","tip":"Good day to be outdoors. Keep windows open for fresh air.","disclaimer":"This is general awareness, not medical advice.","model":{"name":"lightgbm","test_mae":18.065,"target":"mean PM2.5 over the next 24 h"}}
```
`?lang=hi` (same numbers, text in Hindi):
```json
{"reason":"कल हवा संतोषजनक रहने की संभावना है, मुख्य रूप से क्योंकि हाल की बारिश ने हवा साफ़ की है और बारिश का पूर्वानुमान है।","tip":"बाहर जाने के लिए अच्छा दिन है। ताज़ी हवा के लिए खिड़कियाँ खोलें।", "…": "…"}
```

## 3. GET /meta
No inputs. Returns 10 users, 5 institutions and the full `models/metrics.json`.
```json
{"users":[{"id":1,"name":"Aarav Sharma","institution_id":1,"institution":"CSE-DS"},{"id":2,"name":"Diya Patel","institution_id":1,"institution":"CSE-DS"}, "…"],
 "institutions":[{"id":1,"name":"CSE-DS"}, "…"],
 "model_metrics":{"data_source":"openmeteo","rows":37008,"test_period":["2026-03-08","2026-10-25"],"model":{"kind":"lightgbm","target":"mean24","future_weather":true,"target_label":"mean PM2.5 over the next 24 h"}, "…": "…"}}
```

## 4. POST /actions (multipart/form-data)
| Field | Type | Required | Notes |
|---|---|---|---|
| `user_id` | int | yes | must exist (otherwise 404) |
| `action_type` | text | yes | `sapling`, `segregated_bin`, `cleanup` or `dumping_report` (otherwise 400) |
| `lat`, `lon` | float | yes | phone GPS |
| `client_time` | ISO 8601 text | yes | phone time; a time with no zone is treated as UTC |
| `photo` | image file | yes | live camera photo (the "after" photo for a cleanup) |
| `before_photo` | image file | cleanup only | otherwise 400 |

Checks, in order: clock (10 min), geofence (25 km), pHash duplicate (≤ 6 bits). Only if all three pass does YOLOv8n run, followed by the decision (≥ 0.60 approved, ≥ 0.30 needs_review, else rejected). Approved actions get their points straight away.

Plant photo, as a sapling:
```json
{"id":1,"status":"needs_review","confidence":0.421,"points":0,"reasons":["AI is not fully sure — sent to a coordinator"],"detections":[{"name":"tv","conf":0.927,"box":[6.2,166.2,154.5,261.9]}, "…", {"name":"potted plant","conf":0.421,"box":[225.9,177.4,266.6,213.1]}, "…"]}
```
Same photo again:
```json
{"id":2,"status":"rejected","confidence":null,"points":0,"reasons":["this photo (or a near copy) was already submitted"],"detections":[]}
```
Cleanup without `before_photo` (HTTP 400):
```json
{"detail":"cleanup needs a before_photo"}
```

## 5. GET /leaderboard
| Query | Values | Default |
|---|---|---|
| `scope` | `users` \| `institutions` | `institutions` |

Sorting is by `points_week`, then `points_total`, then name. The week runs from Monday 00:00 IST. `progress = min(1, points_week / 50)`.
```json
[{"rank":1,"id":1,"name":"Aarav Sharma","points_total":4,"points_week":4,"goal":50,"progress":0.08},{"rank":2,"id":4,"name":"Ananya Gupta","points_total":0,"points_week":0,"goal":50,"progress":0.0}, "…"]
```

## 6. GET /hotspots
No inputs. Each item is `{"id","lat","lon","created_at","open","cleaned_at"}`. A hotspot is created when a `dumping_report` is approved, and closed by an approved `cleanup` within 150 m.

**Real hotspot lifecycle** (`raw/api_check_hotspots.txt`):
- Throwaway database, real YOLOv8n, 2026-10-29 14:11 UTC.
- Photos: COCO val2017 #4134 (3 litter objects detected) as the dumping report; COCO #285 (no litter) as the cleanup "after".
- Locations were set in the request.

1. `POST /actions` dumping_report at the campus point → `{"id":1,"status":"needs_review","confidence":0.454,"points":0,…}`. The mean of the top-2 litter confidences, 0.454, falls in the 0.30–0.60 review band.
2. `GET /hotspots` before approval:
```json
[]
```
3. `POST /admin/review/1` approve → `{"id":1,"status":"approved","points":2}`.
4. `GET /hotspots` after approval:
```json
[{"id":1,"lat":28.4725,"lon":77.4889,"created_at":"2026-10-29T14:11:22+00:00","open":true,"cleaned_at":null}]
```
5. `POST /actions` cleanup about 55 m north (before = #4134, after = #285) → `{"id":2,"status":"approved","confidence":1.0,"points":5,"reasons":["AI confirmed the action"],"detections":[{"name":"bear","conf":0.964,…}]}`.
6. `GET /hotspots` after the cleanup:
```json
[{"id":1,"lat":28.4725,"lon":77.4889,"created_at":"2026-10-29T14:11:22+00:00","open":false,"cleaned_at":"2026-10-29T14:11:23+00:00"}]
```

Note: step 5 shows a real weakness. The cleanup check only counts litter before and after, so an unrelated "after" photo (here, a bear) was accepted. See `limitations.md`.

## 7. GET /admin/review
Header: `X-Admin-Token: <ADMIN_TOKEN from backend/.env>`. Without it, or with a wrong token, the endpoint returns HTTP 401 `{"detail":"invalid admin token"}`.
```json
[{"id":1,"user_id":1,"user_name":"Aarav Sharma","action_type":"sapling","confidence":0.421,"server_time":"2026-10-29T13:58:43+00:00","lat":28.4725,"lon":77.4889,"photo_url":"/uploads/73274ccbf0f946479ed02c0d9c10e8e2.jpg","before_photo_url":null,"detections":[ "…" ],"reasons":["AI is not fully sure — sent to a coordinator"]}]
```

## 8. POST /admin/review/{id}
- **Header:** `X-Admin-Token`.
- **Body:** `{"decision": "approve" | "reject", "reviewer": "<name>"}`.
- **Errors:** 404 if the action doesn't exist, 409 if it's no longer `needs_review`.
```json
{"id":1,"status":"approved","points":4}
```

## 9. GET /uploads/{file}
Returns the stored photo. Real check: `HTTP 200, image/jpeg, 68032 bytes`.
