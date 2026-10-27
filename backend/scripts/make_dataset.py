"""Merge PM2.5 and weather into one complete hourly table (SPEC §4.3) -> data/hourly.parquet.

Usage (from backend/):
    python scripts/make_dataset.py
"""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_GAP_HOURS = 3
MAIN_COLS = ["pm25", "temp", "rh", "wind_speed"]


def load_csv(name: str) -> pd.DataFrame:
    """Read a raw CSV and index it by UTC hour."""
    df = pd.read_csv(DATA_DIR / name)
    df.index = pd.to_datetime(df.pop("dt"), unit="s", utc=True)
    df.index.name = "time"
    return df


def fill_short_gaps(series: pd.Series, max_gap: int = MAX_GAP_HOURS) -> pd.Series:
    """Linearly interpolate only NaN runs of length <= max_gap; longer gaps stay NaN."""
    is_nan = series.isna()
    run_id = (is_nan != is_nan.shift()).cumsum()
    run_len = is_nan.groupby(run_id).transform("sum")
    short_gap = is_nan & (run_len <= max_gap)
    filled = series.interpolate(method="time", limit_area="inside")
    return series.where(~short_gap, filled)


def pct_missing(df: pd.DataFrame) -> pd.Series:
    """Percentage of missing values per main column."""
    return (df[MAIN_COLS].isna().mean() * 100).round(3)


def main() -> None:
    """Join, reindex to every hour, fill short gaps, and save hourly.parquet."""
    air = load_csv("air_raw.csv").rename(columns={"pm2_5": "pm25"})
    weather = load_csv("weather_raw.csv")
    df = air.join(weather, how="outer")

    start = max(air.index.min(), weather.index.min())
    end = min(air.index.max(), weather.index.max())
    full_range = pd.date_range(start, end, freq="h", tz="UTC", name="time")
    df = df.reindex(full_range)

    before = pct_missing(df)
    for col in df.columns:
        df[col] = fill_short_gaps(df[col])
    after = pct_missing(df)

    df.to_parquet(DATA_DIR / "hourly.parquet")

    print(f"rows: {len(df)}")
    print(f"date range: {df.index.min()} -> {df.index.max()}")
    print("% missing (before -> after filling):")
    for col in MAIN_COLS:
        print(f"  {col:<11} {before[col]:>7} -> {after[col]}")
    print("\n" + df[MAIN_COLS].describe().round(2).to_string())
    print(f"\nsaved: {DATA_DIR / 'hourly.parquet'}")


if __name__ == "__main__":
    main()
