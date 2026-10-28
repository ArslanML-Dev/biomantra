# Bio Mantra (prototype)

Bio Mantra forecasts **tomorrow's PM2.5 and CPCB air-quality category** for the campus area, explains the forecast in one plain English/Hindi sentence (SHAP), and **rewards verified eco-actions**. A live phone photo must pass an anti-fraud gate and a YOLOv8 check. Uncertain cases go to a human reviewer, and verified dumping reports become map hotspots until someone verifies a clean-up.

It's a 3-day B.Tech CSE (Data Science) mini-project prototype: one FastAPI backend, and one React codebase that serves both the website and the Android app (via Capacitor).

## Architecture

```
 Android app (React+Capacitor) ─┐
                                ├──> FastAPI backend ──> SQLite (biomantra.db)
 Website (same React build) ────┘          │
                                           ├── forecast.py  LightGBM + SHAP reason, EN/HI tips, 30-min cache
                                           ├── verify.py    clock → geofence → pHash duplicate → YOLOv8n
                                           └── scoring.py   points, weekly goals, leaderboard, hotspots
 Data: Open-Meteo Air Quality (PM2.5) + Open-Meteo weather archive/forecast (no API key)
```

| Path | What it is |
|---|---|
| `backend/app/` | FastAPI app (`main.py`), config, database, forecast, verification, scoring |
| `backend/scripts/` | data download, dataset merge, EDA, training, AI check, fraud tests |
| `backend/models/` | trained `lgbm.txt`, `feature_list.json`, `metrics.json` (`yolov8n.pt` downloads on first use) |
| `backend/tests/` | pytest suite (32 tests) |
| `frontend/` | React + Vite + TypeScript app, `android/` Capacitor project |
| `docs/` | SPEC, TASKS, progress log, evidence (plots, metrics, test tables) |

## Setup and running

**Quick demo on the laptop + phone:** `powershell -ExecutionPolicy Bypass -File .\start_demo.ps1` (see [docs/DEMO.md](docs/DEMO.md)). The app has a Settings page (⚙) for the Server URL.

Requirements: Python 3.11, Node.js 20+, Git. For the APK you also need Android Studio, opened once so it installs the Android SDK.

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS/Linux
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # CPU torch first
pip install -r requirements.txt
copy .env.example .env            # Windows   (cp .env.example .env on macOS/Linux), then edit values
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -q
```
Rebuild the data and model (optional; the trained model is committed):
```bash
python scripts/fetch_history.py --start 2021-01-01 --source openmeteo
python scripts/fetch_weather.py --start 2021-01-01
python scripts/make_dataset.py
python scripts/eda.py
python scripts/train_forecast.py
```
pandas/pyarrow/numpy/scikit-learn/numba are pinned to older versions on purpose: Windows Smart App Control blocked the newest wheels' DLLs.

### Frontend (website)
```bash
cd frontend
npm install
copy .env.example .env            # set VITE_API_URL=http://<laptop-LAN-IP>:8000
npm run dev -- --host             # open http://<laptop-LAN-IP>:5173 on laptop or phone
npm run build                     # production build in dist/
```

### Android app
```powershell
cd frontend
.\build_apk.ps1                   # npm run build + cap sync + gradle assembleDebug
# APK: frontend\android\app\build\outputs\apk\debug\app-debug.apk
# or: npm run build; npx cap sync android; npx cap open android   (build from Android Studio)
```
Dev builds allow cleartext http to the laptop. For a build against an https backend, run `$env:CAP_RELEASE="1"` first.

### Deploy
- Backend: `render.yaml` (Render free web service), or run locally and expose it with `ngrok http 8000`.
- Website: Vercel with root `frontend/`, `vercel.json` handles SPA routes, and the env var `VITE_API_URL` = backend URL.

## Model results (test set, real numbers from `backend/models/metrics.json`)

Model used by `/forecast`: **LightGBM**. Target: mean PM2.5 over the next 24 h (CPCB bands use 24-h averages). Features: past PM2.5/weather plus next-24 h weather (the actual weather in training, the Open-Meteo forecast live). 37,008 hourly rows, split 70/15/15 in time order. Test period: 2026-03-08 → 2026-10-25.

| Model | MAE | RMSE | R² | Category acc. | Macro-F1 | Recall Poor+ |
|---|---|---|---|---|---|---|
| Persistence | 24.33 | 35.99 | 0.404 | 0.486 | 0.441 | 0.755 |
| Linear regression | 19.53 | 28.79 | 0.619 | 0.583 | 0.491 | 0.728 |
| **LightGBM (used)** | 18.07 | 26.30 | 0.682 | 0.559 | 0.478 | 0.771 |

The original model (PM2.5 at t+24 h, past features only) had LightGBM MAE 30.02, category accuracy 0.399 and Poor+ recall 0.681. It only tied linear regression. The full old-vs-new comparison and its caveats are in [docs/evidence/model_experiments.md](docs/evidence/model_experiments.md). Scores using next-24 h weather are optimistic, because training used the actual weather rather than a forecast. Plots are in `docs/evidence/` (old ones in `docs/evidence/model_v1/`).

## Limitations
- **Modelled data:** PM2.5 comes from Open-Meteo/CAMS model output for a grid cell, not a ground station. History only starts in Aug 2022. No OpenWeather key was used.
- **COCO stand-in classes:** YOLOv8n (COCO) has no sapling or dustbin class. "potted plant" stands in for a sapling, and bottles/cups/bowls/cutlery stand in for litter. Confidence is usually low (a clear plant scored 0.421), so many actions go to human review.
- **Fraud gate:** server time, geofence and a perceptual hash raise the bar but can't stop everything, e.g. a photo of a screen, or GPS spoofing that stays inside the geofence.
- **Prototype scope:** demo users with no passwords, SQLite, and a single campus location.
- Health tips are **general awareness, not medical advice**.

## Credits and licences
- Data: [Open-Meteo](https://open-meteo.com) (CC BY 4.0), which includes Copernicus CAMS air-quality data. Map tiles © OpenStreetMap contributors (ODbL).
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (AGPL-3.0) with COCO-pretrained weights. Test image from [COCO](https://cocodataset.org) (CC BY 4.0).
- LightGBM (MIT), SHAP (MIT), FastAPI (MIT), React (MIT), Leaflet (BSD-2), Capacitor (MIT), imagehash (BSD-2).
- CPCB PM2.5 bands: Central Pollution Control Board, India (National AQI).
