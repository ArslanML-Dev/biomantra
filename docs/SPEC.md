# Bio Mantra: technical specification (prototype)

This is the single source of truth. If something here is wrong or impossible, say so and propose a fix before changing it.

---

## 1. Product in one paragraph
Bio Mantra forecasts tomorrow's air-quality risk for the user's area and explains it in plain English or Hindi. It rewards eco-actions only when a live photo passes an anti-fraud gate and an AI check. Uncertain cases go to a human reviewer. Verified dumping/burning reports become hotspots on a map until someone verifies a clean-up. The user app is an Android app; the website shows the dashboard, map, leaderboard and admin review. Both come from **one React codebase**, packaged with **Capacitor**.

## 2. Architecture
```
 Android app (React+Capacitor) ─┐
                                ├──> FastAPI backend ──> SQLite (biomantra.db)
 Website (same React build) ────┘          │
                                           ├── forecast.py  (LightGBM + SHAP)
                                           ├── verify.py    (time, geofence, pHash, YOLOv8n)
                                           └── scoring.py   (points, goals, leaderboard)
 Data sources: OpenWeather Air Pollution API (PM2.5 history + current)
               Open-Meteo Archive API (hourly weather history, free, no key)
```

## 3. Configuration (`backend/.env`, never committed)
```
OPENWEATHER_API_KEY=xxxx
LAT=28.4744        # placeholder: replace with your campus latitude
LON=77.5040        # placeholder: replace with your campus longitude
GEOFENCE_RADIUS_KM=25
AUTO_APPROVE=0.60
REVIEW_FLOOR=0.30
MAX_CLOCK_SKEW_MIN=10
PHASH_MAX_DISTANCE=6
ADMIN_TOKEN=change-me
```
`backend/app/config.py` reads these values with `python-dotenv`, applies these defaults, and exposes a `settings` object.

## 4. Data

### 4.1 PM2.5 history (OpenWeather)
- Endpoint: `GET http://api.openweathermap.org/data/2.5/air_pollution/history?lat={LAT}&lon={LON}&start={unix}&end={unix}&appid={KEY}`
- Download from **2021-01-01 to today** in **30-day chunks**.
  - Sleep 1 s between calls.
  - Retry 3 times on errors.
- Keep these fields: `dt` (unix, UTC) and `components.pm2_5`. Also keep `pm10`, `no2`, `o3`, `co`, `so2` and `main.aqi` for EDA.
- Save to `backend/data/air_raw.csv`.
- **If the history call fails on the free plan:** stop and tell the user. The fallback is the Open-Meteo Air Quality API: `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=..&longitude=..&hourly=pm2_5,pm10&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`, which needs no key. Record which source was used in `docs/progress.md`.
- Note for the report: both sources are **modelled/reanalysis** concentrations, not ground stations. List this as a limitation.

### 4.2 Weather history (Open-Meteo, free)
- Endpoint: `https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date=2021-01-01&end_date={yesterday}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation&timezone=UTC`
- Save to `backend/data/weather_raw.csv`.

### 4.3 Merged hourly table
- Join the two tables on UTC hour.
- Reindex to a complete hourly range.
- Fill gaps ≤ 3 h by linear interpolation. Leave longer gaps as NaN and drop rows whose target or lags are NaN.
- Save as `backend/data/hourly.parquet`.
- Print: row count, date range, % missing before and after filling.

## 5. Forecast model

### 5.1 Target
`y = pm25` at **t + 24 h**.

### 5.2 Features (all built only from data at time ≤ t)
- `pm25_lag_{1,2,3,6,12,24,48}`
- `pm25_roll_mean_{6,24}`, `pm25_roll_std_24`
- `temp`, `rh`, `wind_speed`, `wind_dir_sin`, `wind_dir_cos`, `precip_24h_sum`
- `hour`, `dow`, `month`, and `is_winter` (Nov–Feb)

### 5.3 Split (time order, never shuffled)
- train: first 70%
- validation: next 15%
- test: last 15%

### 5.4 Models
1. **Persistence:** `y_hat = pm25(t)`.
2. **Linear regression** on the same features (with StandardScaler).
3. **LightGBM regressor:**
   - `n_estimators=2000`, `learning_rate=0.03`, `num_leaves=31`
   - early stopping on validation, 100 rounds
   - `random_state=42`

### 5.5 Metrics (test set)
- **Regression:** MAE, RMSE and R² for all three models.
- **Category:** convert predictions and truth with the CPCB bands below, then report accuracy, macro-F1, and **recall for "Poor" and worse**. Also save a confusion matrix.
- Save to `backend/models/metrics.json` like this:
```json
{"data_source":"openweather","rows":31000,"test_period":["2025-06-01","2026-10-20"],
 "persistence":{"mae":0,"rmse":0,"r2":0},"linear":{"mae":0,"rmse":0,"r2":0},
 "lightgbm":{"mae":0,"rmse":0,"r2":0,"acc_cat":0,"macro_f1":0,"recall_poor_plus":0}}
```
(These numbers are placeholders. Write the real ones.)

### 5.6 Plots, saved to `docs/evidence/`
- `pred_vs_actual.png`: the last 30 days of the test set.
- `confusion_matrix.png`
- `shap_summary.png`
- `feature_importance.png`

### 5.7 CPCB 24-hour PM2.5 bands (µg/m³)
| Range | Category | Tier | Colour |
|---|---|---|---|
| 0–30 | Good | 1 | #00B050 |
| 31–60 | Satisfactory | 1 | #92D050 |
| 61–90 | Moderately polluted | 2 | #FFFF00 |
| 91–120 | Poor | 3 | #FF9900 |
| 121–250 | Very poor | 4 | #FF0000 |
| > 250 | Severe | 4 | #C00000 |

### 5.8 SHAP reason (one sentence)
- Use `shap.TreeExplainer(model)` on the single row being predicted.
- Take the 2 features with the largest positive SHAP value when the forecast is high, or the largest negative when it is low.
- Map each feature to a phrase:

| Feature | English phrase |
|---|---|
| `pm25_lag_*`, `pm25_roll_*` | "recent PM2.5 has been high" (or low) |
| `wind_speed` | "wind is weak" (or strong) |
| `rh` | "humidity is high" |
| `temp` | "it is cold" |
| `is_winter` / `month` | "it is the winter smog season" |
| `precip_24h_sum` | "there has been no rain" |

- Output looks like: `"Tomorrow looks Poor mainly because recent PM2.5 has been high and wind is weak."` Provide a Hindi version from a small template dictionary.

### 5.9 Tips (rule-based, by category)
| Category | English tip | Hindi tip |
|---|---|---|
| Good / Satisfactory | Good day to be outdoors. Keep windows open for fresh air. | बाहर जाने के लिए अच्छा दिन है। ताज़ी हवा के लिए खिड़कियाँ खोलें। |
| Moderately polluted | Sensitive people (asthma, elderly, children) should limit long outdoor exercise. | संवेदनशील लोग (दमा, बुज़ुर्ग, बच्चे) बाहर लंबी कसरत कम करें। |
| Poor | Avoid outdoor exercise. Wear a well-fitting N95 mask outside. Don't burn waste. | बाहर कसरत न करें। बाहर अच्छा N95 मास्क पहनें। कचरा न जलाएँ। |
| Very poor / Severe | Stay indoors if possible, keep windows closed, use a purifier if you have one. Seek medical help for breathing trouble. | हो सके तो घर में रहें, खिड़कियाँ बंद रखें, प्यूरीफ़ायर हो तो चलाएँ। साँस की तकलीफ़ हो तो डॉक्टर से मिलें। |

Always add: **"This is general awareness, not medical advice."** (Hindi: "यह सामान्य जानकारी है, चिकित्सा सलाह नहीं।")

### 5.10 Live inference (`GET /forecast`)
- Fetch the last 72 h of PM2.5: OpenWeather history (start = now − 72 h) plus current conditions.
- Fetch the last 72 h of weather from the Open-Meteo forecast API: `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation&past_days=3&forecast_days=1`.
- Build exactly one feature row with the **same function** used in training (`build_features`).
- Cache the result for 30 minutes.

## 6. Database (SQLite, `backend/biomantra.db`)
```sql
CREATE TABLE institutions (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, institution_id INTEGER REFERENCES institutions(id));
CREATE TABLE actions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  action_type TEXT NOT NULL CHECK (action_type IN ('sapling','segregated_bin','cleanup','dumping_report')),
  photo_path TEXT NOT NULL, before_photo_path TEXT,
  lat REAL NOT NULL, lon REAL NOT NULL,
  client_time TEXT NOT NULL, server_time TEXT NOT NULL,
  phash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('approved','needs_review','rejected')),
  reasons TEXT NOT NULL,            -- JSON list of strings
  confidence REAL, detections TEXT, -- JSON
  model_version TEXT, points INTEGER DEFAULT 0,
  reviewed_by TEXT, reviewed_at TEXT
);
CREATE TABLE hotspots (
  id INTEGER PRIMARY KEY, action_id INTEGER REFERENCES actions(id),
  lat REAL, lon REAL, created_at TEXT, cleaned_action_id INTEGER, cleaned_at TEXT
);
```
**Seed data:**
- **Institutions:** CSE-DS, CSE-AI, CSE-AIML, CSE-IT, ECE.
- **Users:** two per institution, with demo names.

## 7. Verification (`backend/app/verify.py`)
Order matters: run the cheap checks first, AI last.

1. **Clock check:** `abs(server_now - client_time) > MAX_CLOCK_SKEW_MIN` → reject, reason `"photo time does not match server time"`.
2. **Geofence:** haversine distance from (LAT, LON) > `GEOFENCE_RADIUS_KM` → reject, reason `"outside the allowed area"`.
3. **Duplicate:**
   - Compute `imagehash.phash`.
   - If the Hamming distance to any stored phash is ≤ `PHASH_MAX_DISTANCE` → reject, reason `"this photo (or a near copy) was already submitted"`.
4. **AI check** (Ultralytics `YOLO("yolov8n.pt")`, loaded once at startup). Use COCO class **names**, not ids:
   - `sapling`: best confidence of `"potted plant"`.
   - `segregated_bin`: at least 1 litter object (`"bottle"`, `"cup"`, `"bowl"`, `"wine glass"`, `"fork"`, `"knife"`, `"spoon"`) → confidence = the best of those.
     - *Prototype stand-in:* COCO has no "bin" class. Explain this on the About page.
   - `cleanup`: requires `before_photo`; count litter objects (conf ≥ 0.25) before and after. Pass if `after < before`; confidence = `min(1, (before - after) / max(1, before))`.
   - `dumping_report`: at least 2 litter objects; confidence = mean of the top-2 confidences.
5. **Decision:**
   - `conf ≥ AUTO_APPROVE` → **approved**
   - `REVIEW_FLOOR ≤ conf < AUTO_APPROVE` → **needs_review**
   - otherwise → **rejected**, reason `"AI could not confirm the action"`.
6. **Saving:**
   - Save the photo under `backend/uploads/` with a UUID filename.
   - Store detections as `[{"name":..,"conf":..,"box":[x1,y1,x2,y2]}]`.
   - Set `model_version = "yolov8n-coco"`.
   - Return all reasons to the client.

## 8. Scoring (`backend/app/scoring.py`)
| Action | Points when approved |
|---|---|
| sapling | 4 (show "+3 at 30 days, +3 at 90 days: pending re-check") |
| segregated_bin | 2 |
| cleanup | 5. If within 150 m of an open hotspot, also close that hotspot. |
| dumping_report | 2, and create a hotspot |

- **Week:** Monday 00:00 IST to Sunday 23:59 IST.
- **Weekly goal:** 50 points per institution. The leaderboard returns `points_week`, `goal`, `progress = min(1, points_week/goal)`.
- Approving a `needs_review` action in admin gives its points at approval time.

## 9. API contract (FastAPI, JSON, CORS allowed for the web origin and `capacitor://localhost`, `http://localhost`)

`GET /health` → `{"ok": true}`

`GET /forecast?lat=28.47&lon=77.50&lang=en`
```json
{"location":{"lat":28.47,"lon":77.50},"generated_at":"2026-10-28T09:00:00Z",
 "pm25_now":142.0,"pm25_tomorrow":168.3,"category":"Very poor","tier":4,"color":"#FF0000",
 "reason":"Tomorrow looks Very poor mainly because recent PM2.5 has been high and wind is weak.",
 "tip":"Stay indoors if possible ...","disclaimer":"This is general awareness, not medical advice.",
 "model":{"name":"lightgbm","test_mae":0.0}}
```

`POST /actions` (multipart/form-data)
- Fields: `user_id`, `action_type`, `lat`, `lon`, `client_time` (ISO 8601), `photo` (file), `before_photo` (file, cleanup only).
- Response:
```json
{"id":17,"status":"needs_review","confidence":0.48,"points":0,
 "reasons":["AI is not fully sure — sent to a coordinator"],
 "detections":[{"name":"potted plant","conf":0.48,"box":[10,20,200,300]}]}
```

`GET /leaderboard?scope=users|institutions`
```json
[{"rank":1,"id":2,"name":"CSE-DS","points_total":40,"points_week":22,"goal":50,"progress":0.44}]
```

`GET /hotspots` → `[{"id":3,"lat":..,"lon":..,"created_at":"..","open":true}]`

`GET /admin/review` (header `X-Admin-Token`) → the list of `needs_review` actions, with a photo URL and detections.

`POST /admin/review/{id}` with body `{"decision":"approve"|"reject","reviewer":"name"}`.

`GET /meta` → `{"users":[...],"institutions":[...],"model_metrics":{...}}`. This feeds the app's user picker and About page.

Static files: `/uploads/{file}`.

## 10. Frontend (React + Vite + TypeScript, `frontend/`)

**Libraries:** react-router-dom, leaflet + react-leaflet, @capacitor/core, @capacitor/cli, @capacitor/android, @capacitor/camera, @capacitor/geolocation. No UI kit; plain CSS with a green theme (#0E2A1E dark, #C8F169 lime, #F4F3EE light).

`VITE_API_URL` comes from `.env` (the laptop's LAN IP in dev, the Render URL in prod).

**Routes (mobile-first, max-width 480px; wider layouts for /map and /admin):**
1. **`/` Home:**
   - A forecast card with a big PM2.5 tomorrow number, the category chip in its colour, the reason, the tip and the disclaimer.
   - EN/हिं toggle.
   - Buttons "Take action" and "Leaderboard".
2. **`/act` Act:**
   - Choose the action type (4 big buttons).
   - Take a photo with `Camera.getPhoto({source: CameraSource.Camera, resultType: CameraResultType.Uri, quality: 80})`. **Never offer the gallery.** For cleanup, take the "before" and then the "after" photo.
   - Get the position with `Geolocation.getCurrentPosition({enableHighAccuracy: true})`.
   - Turn `photo.webPath` into a Blob, build FormData, then POST to `/actions`.
   - Show a result screen: the status badge, the reasons, the points and the detections list.
   - **On the website (not native):** show "Actions can only be submitted from the Bio Mantra app," using `Capacitor.isNativePlatform()`.
3. **`/leaderboard`:** Users / Institutions tabs, ranked list and weekly progress bars.
4. **`/map`:** a Leaflet map centred on (LAT, LON), with a forecast circle in the category colour and red markers for open hotspots.
5. **`/admin`:**
   - Ask for the token (store it in `sessionStorage`).
   - Review queue cards: photo, detection labels with confidence, and Approve/Reject buttons.
6. **`/about`:**
   - Model metrics from `/meta`, shown as a table vs the baselines.
   - The data sources and their limitations.
   - The "COCO stand-in classes" note.
   - The no-medical-advice note.

**User picker:** the first launch asks "Who are you?" from `/meta` users, stored in `localStorage` (prototype, no passwords).

## 11. Android (Capacitor)
- `npx cap init "Bio Mantra" in.biomantra.app --web-dir=dist`, then `npx cap add android`.
- Permissions in `android/app/src/main/AndroidManifest.xml`: `CAMERA`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `INTERNET`. Follow each plugin's current docs.
- For LAN testing over http, allow cleartext traffic for development only, and remove it for release builds.
- Build a debug APK from Android Studio and install it on a real phone.

## 12. Tests (pytest, `backend/tests/`)
- `test_verify.py`: clock skew rejected; outside geofence rejected; the same image twice → the second is rejected as a duplicate; a slightly resized copy is still caught by pHash; the threshold boundaries 0.30 and 0.60.
- `test_scoring.py`: points by type; the weekly window; a cleanup within 150 m closes the hotspot.
- `test_forecast.py`: `build_features` uses no future data (shift test); the category mapping at band edges (30, 31, 60, 61, 90, 91, 120, 121, 250, 251).
- `test_api.py`: FastAPI TestClient for `/health`, `/leaderboard`, and `/actions` with a sample image (YOLO mocked).

**Manual fraud test (Day 3), recorded in `docs/evidence/test_results.md`:**

| # | Case | Expected |
|---|---|---|
| 1 | Real live photo of a potted plant on campus | approved or needs_review |
| 2 | Same photo submitted again | rejected (duplicate) |
| 3 | Photo of a screen showing a downloaded plant image | record the honest result |
| 4 | GPS spoofed / far location (set via test request) | rejected (geofence) |
| 5 | client_time 2 h old (set via test request) | rejected (clock) |
| 6 | Cleanup with before = littered, after = clean | approved / needs_review |
| 7 | Cleanup with after still littered | rejected |
| 8 | Random photo (wall) as sapling | rejected |

## 13. Deployment for the demo
- **Backend:** Render (free web service), or `ngrok http 8000` from the laptop. A persistent disk isn't needed for the demo.
- **Website:** Vercel, with `VITE_API_URL` set to the backend URL.
- **Demo flow:** website on the projector (`/map` and `/leaderboard`). Take an action on the phone → refresh the website, and the leaderboard and hotspots change. Then show `/admin` approving a `needs_review` action.
