# Bio Mantra: task list (do these in order)

**How to use this file:**
- The user will say "do D1-T1" (or "next task"). Do only that task.
- For each task, follow the **Build** list, run the **Check** command(s), and show the real output.
- Tick the task (`[x]`), add one line to `docs/progress.md`, commit, and stop.
- If a check fails, fix it before ticking.
- Details for every task are in `docs/SPEC.md`; section numbers are given.

---

## Day 1: backend and data-science core

### [x] D1-T1 Project skeleton
**Build:**
- Folders as in CLAUDE.md.
- `backend/requirements.txt`, pinned:
  - fastapi, uvicorn[standard], python-multipart, python-dotenv, requests
  - pandas, pyarrow, numpy, scikit-learn, lightgbm, shap, matplotlib
  - ultralytics, imagehash, pillow, pytest, httpx
- `backend/app/config.py` (SPEC §3).
- `.gitignore` covering `.env`, `.venv`, `data/`, `uploads/`, `*.db`, `models/*.pt`, `node_modules`, `dist`.
- `docs/progress.md`.
- `git init` and a first commit.

**Check:** `python -c "from app.config import settings; print(settings.LAT, settings.LON)"` prints the coordinates.

**Ask the user:** the exact campus latitude/longitude (from Google Maps) and their OpenWeather key. They put the key into `.env` themselves.

### [x] D1-T2 Download PM2.5 history (SPEC §4.1)
**Build:** `backend/scripts/fetch_history.py --start 2021-01-01`. It uses 30-day chunks, retries, a progress print, and writes `data/air_raw.csv`.

**Check:** run it. Print the row count, first/last timestamp and the number of missing hours. If the API refuses history, stop and report it, then implement the Open-Meteo fallback behind `--source openmeteo`.

### [ ] D1-T3 Download weather and merge (SPEC §4.2–4.3)
**Build:** `backend/scripts/fetch_weather.py` and `backend/scripts/make_dataset.py`, which writes `data/hourly.parquet`.

**Check:** print the row count, date range, % missing before/after filling, and `df.describe()` for pm25, temp, rh and wind.

### [ ] D1-T4 EDA plots for the report
**Build:** `backend/scripts/eda.py`, saving 4 plots to `docs/evidence/`:
1. Monthly mean PM2.5 (the seasonality).
2. Mean PM2.5 by hour of day.
3. PM2.5 vs wind speed (scatter + trend).
4. A correlation heatmap.

**Check:** the files exist. Write 3 bullet observations from the real plots into `docs/evidence/eda_notes.md`.

### [ ] D1-T5 Features and training (SPEC §5.1–5.6)
**Build:**
- `app/forecast.py` with:
  - `build_features(df) -> (X, y)`
  - `pm25_to_category(value) -> (category, tier, colour)`
- `scripts/train_forecast.py`:
  - trains persistence, linear and LightGBM
  - writes `models/lgbm.txt` (`model.booster_.save_model`) and `models/feature_list.json`
  - writes `models/metrics.json` and the 4 evidence plots

**Check:** print the metrics table for all 3 models on the test set. LightGBM should beat persistence on MAE. If it doesn't, report that honestly and suggest one change; don't hide it.

### [ ] D1-T6 Forecast tests
**Build:** `tests/test_forecast.py` (SPEC §12): a no-future-leakage test and the band-edge tests.

**Check:** `pytest -q tests/test_forecast.py` passes.

### [ ] D1-T7 `/forecast` endpoint (SPEC §5.8–5.10, §9)
**Build:**
- In `app/main.py`: the FastAPI app, CORS, `/health` and `/forecast` with `lang=en|hi`.
- In `app/forecast.py`: the SHAP reason, the tips and a 30-minute cache.

**Check:** run `uvicorn ...`, then `curl "localhost:8000/forecast?lang=en"` and `?lang=hi`, and show both JSON responses.

### [ ] D1-T8 Database and seed (SPEC §6)
**Build:** `app/db.py` (create the tables and seed them on startup if empty) and `GET /meta`.

**Check:** `curl localhost:8000/meta` shows 5 institutions and 10 users.

### [ ] D1-T9 Verification pipeline (SPEC §7)
**Build:**
- `app/verify.py` with these pure functions:
  - `check_clock`
  - `check_geofence`
  - `check_duplicate`
  - `ai_check`
  - `decide`
- YOLO loaded once.
- `tests/test_verify.py` (SPEC §12), with YOLO mocked in the tests.

**Check:** `pytest -q tests/test_verify.py` passes. Then run `ai_check` on 2 real local images (a plant, a wall) and print the detections.

### [ ] D1-T10 `/actions`, scoring, leaderboard, hotspots, admin (SPEC §8–9)
**Build:** `app/scoring.py`, the remaining endpoints, the `/uploads` static route and `tests/test_scoring.py` + `tests/test_api.py`.

**Check:**
- `pytest -q` passes (all tests).
- Then `curl -F` a sample photo to `/actions` and show the response, then `/leaderboard`.

**End of Day 1:** commit, and summarise in `docs/progress.md` what works and what doesn't.

---

## Day 2: the app (React + Capacitor)

### [ ] D2-T1 React app skeleton
**Build:**
- Vite React TypeScript in `frontend/`, with react-router.
- `src/api.ts` (fetch helpers using `VITE_API_URL`).
- `src/i18n.ts` (EN/HI strings).
- A green theme CSS.
- The layout with a bottom nav: Home · Act · Leaderboard · Map.

**Check:** `npm run dev -- --host` opens on the laptop and on the phone browser via the LAN IP.

### [ ] D2-T2 User picker + Home screen (SPEC §10.1)
**Check:** the forecast card shows real data from the backend, and the EN/हिं toggle works. Take a screenshot to `docs/evidence/screens/`.

### [ ] D2-T3 Leaderboard screen
**Check:** both tabs render from `/leaderboard`; the progress bars match `points_week/goal`.

### [ ] D2-T4 Capacitor Android setup (SPEC §11)
**Build:** install the Capacitor packages, init, add android, add permissions, and configure the dev server or API URL.

**Check:** the debug APK installs on a real phone and opens the Home screen with live data.

### [ ] D2-T5 Act screen with live camera + GPS (SPEC §10.2)
**Check, on the phone:**
- Submit a real sapling/plant photo and see the result screen with the status and reasons.
- Submit the same scene twice and see the second one rejected as a duplicate.
- On the website, the Act page shows the "app only" message.

### [ ] D2-T6 Cleanup flow (before + after)
**Check:** the before/after submission works end to end, and the result is shown.

**End of Day 2:** take screenshots of every screen on the phone, then commit and summarise.

---

## Day 3: website, admin, deploy and testing

### [ ] D3-T1 Map page (SPEC §10.4)
**Check:** a dumping report approved via admin appears as a hotspot. A verified cleanup within 150 m closes it.

### [ ] D3-T2 Admin page (SPEC §10.5)
**Check:** a `needs_review` action can be approved, and its points appear on the leaderboard.

### [ ] D3-T3 About page (SPEC §10.6)
**Check:** it shows the real metrics from `models/metrics.json`, the data sources, the limitations and the disclaimers.

### [ ] D3-T4 Deploy
**Build:** the backend on Render or ngrok, and the website on Vercel. The app points at the public backend URL; rebuild the APK.

**Check:** the phone works on mobile data (not only Wi-Fi), and the website opens on another laptop.

### [ ] D3-T5 Fraud test table (SPEC §12, manual)
**Check:** fill `docs/evidence/test_results.md` with the **real** result of all 8 cases, including failures, and a short "what we learned" section.

### [ ] D3-T6 Demo rehearsal + README
**Build:**
- `README.md`: what it is, setup steps, how to run, architecture, model results table, limitations, credits/licences.
- `docs/evidence/changes_from_synopsis.md`.

**Check:** run the demo flow (SPEC §13) twice from a fresh start, with no errors.

---

## Stretch (only after D3-T6 is done)

### [ ] S1 Fire feature (NASA FIRMS)
Add a fire count within 200 km to the NW over the last 24/48 h as features. Retrain, and compare MAE with and without the fire features. Record both results.

### [ ] S2 3D globe map (inspired by God's Eye View)
Check the repo licence first. Show the forecast, hotspots and fires on a CesiumJS/deck.gl globe on the website, keeping Leaflet as the fallback.

### [ ] S3 Push alert when tomorrow is Poor or worse

### [ ] S4 Offline action queue with server time checks
