# Bio Mantra: instructions for Claude Code

You are helping a team of 4 B.Tech CSE (Data Science) students build a **3-day prototype** of Bio Mantra for their mini project. They will submit the prototype and a 40-page report, and defend both in a viva.

**Read these before any work:**
1. `docs/SPEC.md`: exact technical details (data, model, API, database, screens, tests). Treat it as the source of truth.
2. `docs/TASKS.md`: the ordered task list. Do one task at a time.
3. `docs/progress.md`: what has been done so far. Create it if it's missing.

## What Bio Mantra does
1. **Forecasts** tomorrow's PM2.5 and CPCB AQI category for the campus area, using a LightGBM model trained on real hourly data.
2. **Explains** it with a one-line SHAP reason and a simple English/Hindi tip (awareness, not medical advice).
3. **Rewards verified eco-actions:**
   - The **Android app** (React + Capacitor) takes a **live camera photo** with GPS.
   - The backend runs an anti-fraud gate (server time, geofence, perceptual-hash duplicate check) and YOLOv8.
   - Confident results are approved, uncertain ones go to a human reviewer, and the rest are rejected.
   - Verified dumping reports become map hotspots until a verified clean-up.
4. **Website:** the same React code serves the map, leaderboard, admin review and About page.

## Stack (don't change without asking)
- **Backend:** Python 3.11, FastAPI, SQLite, pandas, LightGBM, SHAP, Ultralytics YOLOv8n (pretrained), imagehash.
- **Frontend:** React + Vite + TypeScript, packaged with Capacitor (camera, geolocation) for Android, and deployed as a website.
- **Data:** OpenWeather Air Pollution API, with Open-Meteo as a free fallback, and Open-Meteo for weather.

## Working rules
1. **One task at a time.**
   - Start by restating the task and listing the files you'll touch.
   - For anything bigger than one file, show a short plan and wait for "go".
2. **Build → run → show the real output → stop.**
   - Never claim something works without running it.
   - Never invent metrics, test results or screenshots.
3. **Definition of done:**
   - The task's Check passes and you show the command and its output.
   - Tick the task in TASKS.md.
   - Add one line to `docs/progress.md`: date, task, result, how it was checked.
   - Make a git commit (`feat: ...`, `fix: ...`, `test: ...`).
4. **When something fails:** show the error, explain the cause in one sentence, fix it, re-run. If it's blocked (API key, licence, hardware), stop and tell the user exactly what they need to do.
5. **Simple code for students:**
   - Short functions, each with a one-line docstring.
   - Clear names and type hints in Python.
   - No clever tricks.
   - After creating a file, explain in 2–3 lines what it does, for the viva.
6. **Dependencies:** pin versions. Ask before adding anything not listed in SPEC.md.
7. **Secrets:** read them from `backend/.env` only. Never print or commit them. Ask the user to paste the keys into `.env` themselves.
8. **Honesty in the product:**
   - The About page must state the limitations: modelled data, COCO stand-in classes, prototype scope.
   - Health text is always "awareness, not medical advice".
9. **Evidence for the report:** save plots, metrics, test tables and screenshots in `docs/evidence/` as you go (see TASKS.md).
10. **Platform:** the user may be on Windows. Give commands for both Windows (PowerShell) and macOS/Linux where they differ.

## Commands (keep this list up to date)
```
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -q

# frontend
cd frontend && npm install
npm run dev -- --host
npm run build && npx cap sync android && npx cap open android
powershell -ExecutionPolicy Bypass -File .setup_android_sdk.ps1   # one-time: Android SDK + JDK 21, no Android Studio UI
.\build_apk.ps1                # Windows: one-step debug APK (needs Android SDK)

# backend scripts (from backend/)
python scripts/eda.py
python scripts/train_forecast.py
python scripts/check_ai.py sapling plant.jpg wall.jpg
python scripts/fraud_tests.py --plant p.jpg --wall w.jpg
```

## Out of scope
Passwords/auth (use the simple user picker), payments, IHIP health data, LSTM, iOS builds, voice interface. Stretch goals are listed at the end of TASKS.md; do them only when asked and only after Day 3 is complete.
