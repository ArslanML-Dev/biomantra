# EDA notes (from `backend/scripts/eda.py`, data: Open-Meteo modelled PM2.5, 2022-08-04 → 2026-10-26)

- **Strong winter seasonality.** Monthly mean PM2.5 peaks in Jan (120.5 µg/m³), Dec (109.6) and Nov (105.1), and is lowest in the monsoon months Jul–Sep (45.0, 48.1, 44.9). Winter means are roughly 2.5× the monsoon means. See `eda_monthly_pm25.png`.
- **Clear daily cycle.** Mean PM2.5 is highest late evening/night (22:00 IST: 93.3) and lowest mid-afternoon (15:00 IST: 56.2), consistent with a shallow night-time boundary layer trapping pollution. See `eda_hourly_pm25.png`.
- **Wind and temperature dilute, co-pollutants move together.** Mean PM2.5 falls from 100.0 at 0–2 km/h wind to ~63–67 at 12–24 km/h (correlation −0.17); temperature has the strongest negative weather correlation (−0.38); PM10 and CO correlate +0.59 with PM2.5. See `eda_pm25_vs_wind.png` and `eda_correlation.png`.
