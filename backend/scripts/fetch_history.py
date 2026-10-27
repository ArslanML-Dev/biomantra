"""Download hourly PM2.5 history (SPEC §4.1) into data/air_raw.csv.

Usage (from backend/):
    python scripts/fetch_history.py --start 2021-01-01                     # OpenWeather (needs key)
    python scripts/fetch_history.py --start 2021-01-01 --source openmeteo  # free fallback, no key
"""
import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "air_raw.csv"
OPENWEATHER_URL = "http://api.openweathermap.org/data/2.5/air_pollution/history"
OPENMETEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENMETEO_FIELDS = {
    "pm2_5": "pm2_5", "pm10": "pm10", "nitrogen_dioxide": "no2",
    "ozone": "o3", "carbon_monoxide": "co", "sulphur_dioxide": "so2",
}
CHUNK_DAYS = 30
RETRIES = 3


def get_json(url: str, params: dict) -> dict:
    """GET a URL and return JSON, retrying up to RETRIES times."""
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as err:
            print(f"  attempt {attempt}/{RETRIES} failed: {err}")
            if attempt == RETRIES:
                raise
            time.sleep(5 * attempt)
    return {}


def date_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into consecutive 30-day (start, end) pairs."""
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=CHUNK_DAYS - 1), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks


def fetch_openweather_chunk(start: date, end: date) -> pd.DataFrame:
    """Fetch one chunk from the OpenWeather air pollution history API."""
    start_ts = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
    end_ts = int(datetime(end.year, end.month, end.day, 23, tzinfo=timezone.utc).timestamp())
    data = get_json(OPENWEATHER_URL, {
        "lat": settings.LAT, "lon": settings.LON,
        "start": start_ts, "end": end_ts, "appid": settings.OPENWEATHER_API_KEY,
    })
    rows = []
    for item in data.get("list", []):
        comp = item["components"]
        rows.append({
            "dt": item["dt"], "pm2_5": comp.get("pm2_5"), "pm10": comp.get("pm10"),
            "no2": comp.get("no2"), "o3": comp.get("o3"), "co": comp.get("co"),
            "so2": comp.get("so2"), "aqi": item["main"].get("aqi"),
        })
    return pd.DataFrame(rows)


def fetch_openmeteo_chunk(start: date, end: date) -> pd.DataFrame:
    """Fetch one chunk from the Open-Meteo Air Quality API (UTC hours)."""
    data = get_json(OPENMETEO_URL, {
        "latitude": settings.LAT, "longitude": settings.LON,
        "hourly": ",".join(OPENMETEO_FIELDS), "timezone": "GMT",
        "start_date": start.isoformat(), "end_date": end.isoformat(),
    })
    hourly = data.get("hourly", {})
    df = pd.DataFrame({new: hourly.get(old) for old, new in OPENMETEO_FIELDS.items()})
    times = pd.to_datetime(hourly.get("time", []), utc=True)
    df.insert(0, "dt", times.astype("int64") // 10**9)
    return df


def main() -> None:
    """Download all chunks, de-duplicate, and save data/air_raw.csv."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--source", choices=["openweather", "openmeteo"], default="openweather")
    args = parser.parse_args()

    if args.source == "openweather" and not settings.OPENWEATHER_API_KEY:
        sys.exit("No OPENWEATHER_API_KEY in backend/.env. Add it, or use --source openmeteo.")

    fetch_chunk = fetch_openweather_chunk if args.source == "openweather" else fetch_openmeteo_chunk
    chunks = date_chunks(date.fromisoformat(args.start), date.today())
    frames = []
    for i, (start, end) in enumerate(chunks, 1):
        df = fetch_chunk(start, end)
        frames.append(df)
        print(f"[{i}/{len(chunks)}] {start} -> {end}: {len(df)} rows")
        time.sleep(1)

    frames = [df.dropna(subset=["pm2_5"]) for df in frames]
    air = pd.concat([df for df in frames if not df.empty]).drop_duplicates("dt").sort_values("dt")
    now_ts = int(datetime.now(timezone.utc).timestamp())
    air = air[air["dt"] <= now_ts]  # drop any forecast hours the API pads on
    if air.empty:
        sys.exit("No PM2.5 rows returned. Check the source, dates and network.")
    OUT_PATH.parent.mkdir(exist_ok=True)
    air.to_csv(OUT_PATH, index=False)

    times = pd.to_datetime(air["dt"], unit="s", utc=True)
    expected = int((times.max() - times.min()) / pd.Timedelta(hours=1)) + 1
    print(f"\nsource: {args.source}")
    print(f"rows: {len(air)}")
    print(f"first: {times.min()}  last: {times.max()}")
    print(f"missing hours: {expected - len(air)} of {expected}")
    print(f"saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
