"""EDA plots for the report (D1-T4) -> docs/evidence/eda_*.png.

Usage (from backend/):
    python scripts/eda.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BACKEND_DIR / "data" / "hourly.parquet"
EVIDENCE_DIR = BACKEND_DIR.parent / "docs" / "evidence"


def load_ist() -> pd.DataFrame:
    """Load hourly.parquet with the index converted to India time (IST)."""
    df = pd.read_parquet(DATA_PATH)
    df.index = df.index.tz_convert("Asia/Kolkata")
    return df


def plot_monthly(df: pd.DataFrame) -> pd.Series:
    """Bar chart of mean PM2.5 per calendar month (seasonality)."""
    monthly = df.groupby(df.index.month)["pm25"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(monthly.index, monthly.values, color="#4C9A2A")
    ax.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylabel("Mean PM2.5 (µg/m³)")
    ax.set_title("Monthly mean PM2.5 (all years)")
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "eda_monthly_pm25.png", dpi=120)
    plt.close(fig)
    return monthly


def plot_hourly(df: pd.DataFrame) -> pd.Series:
    """Line chart of mean PM2.5 by hour of day (IST)."""
    hourly = df.groupby(df.index.hour)["pm25"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(hourly.index, hourly.values, marker="o", color="#0E2A1E")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hour of day (IST)")
    ax.set_ylabel("Mean PM2.5 (µg/m³)")
    ax.set_title("Mean PM2.5 by hour of day")
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "eda_hourly_pm25.png", dpi=120)
    plt.close(fig)
    return hourly


def plot_wind(df: pd.DataFrame) -> pd.Series:
    """Scatter of PM2.5 vs wind speed with a binned-mean trend line."""
    sample = df.sample(min(5000, len(df)), random_state=42)
    bins = pd.cut(df["wind_speed"], bins=np.arange(0, df["wind_speed"].max() + 2, 2))
    trend = df.groupby(bins, observed=True)["pm25"].mean()
    centres = [b.mid for b in trend.index]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(sample["wind_speed"], sample["pm25"], s=4, alpha=0.3, color="#4C9A2A")
    ax.plot(centres, trend.values, color="red", linewidth=2, label="mean per 2 km/h bin")
    ax.set_xlabel("Wind speed at 10 m (km/h)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("PM2.5 vs wind speed")
    ax.legend()
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "eda_pm25_vs_wind.png", dpi=120)
    plt.close(fig)
    return trend


def plot_corr(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation heatmap of pollutants and weather variables."""
    corr = df.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)), corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax)
    ax.set_title("Correlation heatmap")
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "eda_correlation.png", dpi=120)
    plt.close(fig)
    return corr


def main() -> None:
    """Make all 4 EDA plots and print the numbers behind them."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    df = load_ist()
    print("monthly mean PM2.5:\n", plot_monthly(df).round(1).to_string())
    print("\nhourly mean PM2.5 (IST):\n", plot_hourly(df).round(1).to_string())
    print("\nPM2.5 by wind bin:\n", plot_wind(df).round(1).to_string())
    print("\ncorrelation with pm25:\n", plot_corr(df)["pm25"].round(2).to_string())
    print(f"\nsaved 4 plots to {EVIDENCE_DIR}")


if __name__ == "__main__":
    main()
