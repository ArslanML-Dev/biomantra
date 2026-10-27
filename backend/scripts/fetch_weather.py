"""Download hourly weather history from Open-Meteo Archive (SPEC §4.2) into data/weather_raw.csv.

Usage (from backend/):
    python scripts/fetch_weather.py --start 2021-01-01
"""
import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402
from scripts.fetch_history import get_json  # noqa: E402

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "weather_raw.csv"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FIELDS = {
    "temperature_2m": "temp", "relative_humidity_2m": "rh", "wind_speed_10m": "wind_speed",
    "wind_direction_10m": "wind_dir", "precipitation": "precip",
}


def year_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into calendar-year (start, end) pairs."""
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(date(cur.year, 12, 31), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks


def fetch_chunk(start: date, end: date) -> pd.DataFrame:
    """Fetch one chunk of hourly weather (UTC) from the archive API."""
    data = get_json(ARCHIVE_URL, {
        "latitude": settings.LAT, "longitude": settings.LON,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "hourly": ",".join(FIELDS), "timezone": "UTC",
    })
    hourly = data.get("hourly", {})
    df = pd.DataFrame({new: hourly.get(old) for old, new in FIELDS.items()})
    times = pd.to_datetime(hourly.get("time", []), utc=True)
    df.insert(0, "dt", times.astype("int64") // 10**9)
    return df


def main() -> None:
    """Download all years and save data/weather_raw.csv."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2021-01-01")
    args = parser.parse_args()

    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    chunks = year_chunks(date.fromisoformat(args.start), yesterday)
    frames = []
    for i, (start, end) in enumerate(chunks, 1):
        df = fetch_chunk(start, end)
        frames.append(df)
        print(f"[{i}/{len(chunks)}] {start} -> {end}: {len(df)} rows")
        time.sleep(1)

    weather = pd.concat(frames).drop_duplicates("dt").sort_values("dt")
    weather = weather.dropna(subset=list(FIELDS.values()), how="all")
    OUT_PATH.parent.mkdir(exist_ok=True)
    weather.to_csv(OUT_PATH, index=False)

    times = pd.to_datetime(weather["dt"], unit="s", utc=True)
    print(f"\nrows: {len(weather)}")
    print(f"first: {times.min()}  last: {times.max()}")
    print(f"saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
