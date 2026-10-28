# Bio Mantra handoff (2026-10-29)

Everything that could be built and checked on the laptop without a phone, accounts or a browser is done and committed. This file lists what works, what didn't, and every step left for you, in order.

> **Update 2026-10-29:** the quickest path is now [DEMO.md](DEMO.md): `start_demo.ps1` starts everything and prints the phone addresses, and the app has a ⚙ Settings page for the Server URL, so no rebuild is needed when the IP changes. Screenshots of every page are in `docs/evidence/screens/`.

---

## 1. What works (real, checked results)

| Area | Result | How it was checked |
|---|---|---|
| Data | 37,080 merged hourly rows, 2022-08-04 → 2026-10-26 UTC, 0 % missing (Open-Meteo) | `make_dataset.py` output |
| EDA (D1-T4) | 4 plots + notes. Jan mean 120.5 vs Sep 44.9 µg/m³; night peak 93.3 at 22:00 IST | `docs/evidence/eda_*.png`, `eda_notes.md` |
| Forecast model (D1-T5) | Test MAE: persistence 33.66, linear 29.97, **LightGBM 30.02** (RMSE 44.16, R² 0.363, Poor+ recall 0.681) | `train_forecast.py`, `backend/models/metrics.json`, 4 plots |
| `/forecast` (D1-T7) | Live EN + HI, e.g. "Tomorrow looks Poor mainly because recent PM2.5 has been high and the usual daily pattern pushes it up." | curl |
| DB + `/meta` (D1-T8) | 5 institutions, 10 users seeded | curl |
| Fraud gate + YOLO (D1-T9/T10) | COCO plant → needs_review 0.421; synthetic wall → rejected; duplicate, geofence and clock all rejected | `docs/evidence/ai_check_samples.md`, `api_check_d1.md`, `test_results.md` |
| Scoring/leaderboard/hotspots/admin | Admin approve → +4 points on the leaderboard; cleanup within 150 m closes a hotspot | pytest + live curl |
| Tests | **32 passed** (`pytest -q`) | dataset, forecast, verify, scoring, API |
| Website (D2-T1…D3-T3) | Home (forecast card, EN/हिं), user picker, Leaderboard, Act (app-only message on web), Map, Admin, About | `npm run build` OK; dev server answers on http://192.168.1.19:5173 |
| Android project (D2-T4) | Capacitor 7, app id `in.biomantra.app`, CAMERA + location permissions, dev-only cleartext | `npx cap add/sync android` OK |
| Demo flow (API level) | Run twice from a fresh DB with 0 server errors | `docs/evidence/demo_rehearsal.md` |
| Deploy files | `render.yaml`, `frontend/vercel.json` | committed, **not deployed** |

## 2. What failed or is weak, and why

1. ~~No APK was built.~~ **Fixed (round 3):** the SDK was installed without the Android Studio UI (`frontend/setup_android_sdk.ps1`), plus a portable JDK 21, because Android Studio's Java 25 is too new for Gradle 8.11. `BioMantra.apk` is now built. No phone was connected over USB, so it isn't installed yet, and every on-phone check (D2-T4, T5, T6, D3-T4) is still untested.
2. ~~LightGBM only ties linear regression.~~ **Improved (round 3):** the target is now the next-24 h mean, with next-24 h weather features. LightGBM test MAE is 18.07 vs linear 19.53 vs persistence 24.33, and category accuracy went from 0.399 to 0.559 (see `docs/evidence/model_experiments.md`). The scores with weather features are optimistic, because training used the actual weather rather than a forecast.
3. **The AI is unsure about real plants.** A clear potted plant scored 0.421 (needs_review), because COCO has no sapling/bin classes. Expect most real actions to need admin approval. That's by design, and it's explained on the About page.
4. **No OpenWeather key**, so all data is Open-Meteo modelled data starting Aug 2022 (not 2021).
5. **Fraud cases 3, 6, 7** weren't run: they need real phone photos. Cases 1/2/8 used stand-in images (a COCO photo and a synthetic wall).
6. **No screenshots** were taken, because browser automation wasn't allowed.
7. **Nothing is deployed:** no git remote, no accounts, and ngrok isn't installed. The Render free tier has 512 MB RAM, and torch + YOLO may not fit. ngrok from the laptop is the safer demo option.

## 3. WAITING FOR USER: do these in order (one sitting)

Open PowerShell. Every command below starts from `C:\dev\BIO-MANTRA-PROTOTYPE`.

### A. Start the backend and website on the laptop
1. `cd backend; .venv\Scripts\activate; uvicorn app.main:app --host 0.0.0.0 --port 8000`. Leave this window open.
2. In a second window: `cd frontend; npm run dev -- --host`.
3. If Windows Firewall asks, click **Allow** for Python and Node on **Private networks**.
4. On the phone (same Wi-Fi), open `http://192.168.1.19:5173`. If your IP has changed, run `ipconfig` and use the Wi-Fi IPv4 address, and also update `frontend\.env` → `VITE_API_URL=http://<IP>:8000`.
5. Check: pick a user → the Home card shows a forecast → tap EN/हिं → open Leaderboard (both tabs), Map, About. Open Act: it should say "Actions can only be submitted from the Bio Mantra app."

### B. Screenshots (D2-T2, end of Day 2)
6. On the laptop, take screenshots of Home (EN and हिं), Leaderboard (both tabs), Map, About and Admin. Save them to `docs\evidence\screens\`.

### C. Install the app on the phone (D2-T4)
7. The APK is already built: `C:\dev\BIO-MANTRA-PROTOTYPE\BioMantra.apk`.
8. Install it, either by copying the file to the phone and opening it (allow "install unknown apps"), or over USB (USB debugging on, then `& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r BioMantra.apk`).
9. Open Bio Mantra → ⚙ → Server URL = the "PHONE APP" address that `start_demo.ps1` prints → Test connection → Save.
10. Pick a user → check the Home screen shows live data.

### D. Phone action tests (D2-T5, D2-T6)
12. Act → "Planted a sapling" → allow camera and location → photograph a real plant → see the result screen (status, reasons, points).
13. Photograph the **same scene** again → it should be rejected as a duplicate. If it isn't (the phone moved too much), note the honest result.
14. Act → "Cleaned up a spot" → take the BEFORE photo of some litter (bottles/cups) → remove it → take the AFTER photo → see the result.
15. On the laptop, open `http://localhost:5173/admin` → token `change-me` (or your `ADMIN_TOKEN`) → approve a needs_review item → confirm its points on the Leaderboard.
16. Phone screenshots of every screen → `docs\evidence\screens\`.

### E. Fraud test with real photos (D3-T5)
17. Take these phone photos on campus and copy them to the laptop: `plant.jpg`, `wall.jpg`, `screen.jpg` (a laptop screen showing a downloaded plant image), `littered.jpg`, `clean.jpg` (same spot, cleaned) and `still_littered.jpg`.
18. Stop the backend, delete `backend\biomantra.db`, and start the backend again.
19. `cd backend; python scripts\fraud_tests.py --plant plant.jpg --wall wall.jpg --screen screen.jpg --before littered.jpg --after-clean clean.jpg --after-dirty still_littered.jpg`
20. Paste the printed table into **Run 2** in `docs\evidence\test_results.md` (keep any failures), and add a line to "What we learned".

### F. Deploy (D3-T4). Pick ONE backend option
21. **Option 1, ngrok (recommended):** create a free account at ngrok.com → install ngrok → `ngrok config add-authtoken <your token>` → `ngrok http 8000`. Copy the `https://….ngrok-free.app` URL.
    **Option 2, Render:** create a GitHub repo → `git remote add origin <url>; git push -u origin master` → in Render choose **New → Blueprint** and pick the repo (it reads `render.yaml`) → set `ADMIN_TOKEN` to a secret value → wait for `/health` to go green. If it runs out of memory on the free plan, use ngrok.
22. In `backend\.env`, change `ADMIN_TOKEN` from `change-me` to your own secret before the demo.
23. **Website on Vercel:** push to GitHub (if not done) → vercel.com → New Project → import the repo → Root Directory `frontend` → add the environment variable `VITE_API_URL=<backend https URL>` → Deploy.
24. **APK for the demo:** set `frontend\.env` → `VITE_API_URL=<backend https URL>`, then run `$env:CAP_RELEASE="1"; .\build_apk.ps1` and reinstall the APK.
25. Check: the phone works on **mobile data** (Wi-Fi off), and the Vercel site opens on another laptop.

### G. Final rehearsal (D3-T6)
26. Run the SPEC §13 demo twice from a fresh start: delete `biomantra.db` and restart the backend → website `/map` + `/leaderboard` on the projector → submit an action on the phone → refresh the site → approve a needs_review item in `/admin` → the points change.
27. Add the original synopsis items to `docs\evidence\changes_from_synopsis.md` (the synopsis wasn't in the repo).
28. For each task you finish here: tick it in `docs\TASKS.md`, add a line to `docs\progress.md`, and commit.
