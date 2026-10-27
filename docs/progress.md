# Progress log
One line per finished task: date · task · result · how it was checked.
2026-10-28 · D1-T1 Project skeleton · done: config, .env, .gitignore, pinned requirements (Py 3.11.9, CPU torch 2.14.1) · checked: `python -c "from app.config import settings; print(settings.LAT, settings.LON)"` → 28.4725 77.4889
2026-10-28 · D1-T2 PM2.5 history · source: openmeteo (no OpenWeather key yet); 37,099 hourly rows, 2022-08-04 00:00 → 2026-10-27 18:00 UTC, 0 missing hours (Open-Meteo PM2.5 history starts 2022-08-04, so 2021 requests were empty); also pinned older pandas/pyarrow/numpy/sklearn/numba because Windows Smart App Control blocked the newest wheels · checked: ran scripts/fetch_history.py --source openmeteo
