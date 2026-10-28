"""Forecast features, CPCB categories, SHAP reasons and live inference (SPEC §5)."""
import numpy as np
import pandas as pd

LAGS = [1, 2, 3, 6, 12, 24, 48]
HORIZON_H = 24
WINTER_MONTHS = [11, 12, 1, 2]

# (upper bound µg/m³, category, tier, colour) — SPEC §5.7
BANDS = [
    (30, "Good", 1, "#00B050"),
    (60, "Satisfactory", 1, "#92D050"),
    (90, "Moderately polluted", 2, "#FFFF00"),
    (120, "Poor", 3, "#FF9900"),
    (250, "Very poor", 4, "#FF0000"),
    (float("inf"), "Severe", 4, "#C00000"),
]
CATEGORIES = [b[1] for b in BANDS]


def pm25_to_category(value: float) -> tuple[str, int, str]:
    """Map a PM2.5 value to its CPCB (category, tier, colour)."""
    for upper, name, tier, colour in BANDS:
        if value <= upper:
            return name, tier, colour
    return BANDS[-1][1:]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build the feature table X (data at time <= t only) and target y = pm25(t+24h).

    df needs an hourly UTC DatetimeIndex and columns pm25, temp, rh, wind_speed, wind_dir, precip.
    Rows with NaN are kept; the caller drops them for training or takes the last row for live use.
    """
    df = df.asfreq("h")
    pm = df["pm25"]
    X = pd.DataFrame(index=df.index)
    for lag in LAGS:
        X[f"pm25_lag_{lag}"] = pm.shift(lag)
    X["pm25_roll_mean_6"] = pm.rolling(6).mean()
    X["pm25_roll_mean_24"] = pm.rolling(24).mean()
    X["pm25_roll_std_24"] = pm.rolling(24).std()
    X["temp"] = df["temp"]
    X["rh"] = df["rh"]
    X["wind_speed"] = df["wind_speed"]
    X["wind_dir_sin"] = np.sin(np.radians(df["wind_dir"]))
    X["wind_dir_cos"] = np.cos(np.radians(df["wind_dir"]))
    X["precip_24h_sum"] = df["precip"].rolling(24).sum()
    local = df.index.tz_convert("Asia/Kolkata")
    X["hour"] = local.hour
    X["dow"] = local.dayofweek
    X["month"] = local.month
    X["is_winter"] = local.month.isin(WINTER_MONTHS).astype(int)
    y = pm.shift(-HORIZON_H).rename("y")
    return X, y
