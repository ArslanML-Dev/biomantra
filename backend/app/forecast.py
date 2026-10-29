"""Forecast features, CPCB categories, SHAP reasons and live inference (SPEC §5)."""
import json
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import requests

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


def future_weather(df: pd.DataFrame) -> pd.DataFrame:
    """Weather over the NEXT 24 h (t+1 .. t+24): means, and the rain total.

    In training these are the actual observed values, used as a stand-in for a weather forecast.
    At live inference they come from the Open-Meteo weather forecast. No future PM2.5 is used.
    """
    return pd.DataFrame({
        "fut_temp_mean24": next24_mean(df["temp"]),
        "fut_rh_mean24": next24_mean(df["rh"]),
        "fut_wind_speed_mean24": next24_mean(df["wind_speed"]),
        "fut_wind_dir_sin_mean24": next24_mean(np.sin(np.radians(df["wind_dir"]))),
        "fut_wind_dir_cos_mean24": next24_mean(np.cos(np.radians(df["wind_dir"]))),
        "fut_precip_sum24": df["precip"].rolling(HORIZON_H).sum().shift(-HORIZON_H),
    }, index=df.index)


def next24_mean(series: pd.Series) -> pd.Series:
    """At each hour t, the mean of the series over t+1 .. t+24."""
    return series.rolling(HORIZON_H).mean().shift(-HORIZON_H)


def make_target(pm: pd.Series, target: str) -> pd.Series:
    """Target y: "t24" = PM2.5 at t+24 h; "mean24" = mean PM2.5 over t+1 .. t+24 h."""
    if target == "mean24":
        return next24_mean(pm).rename("y")
    return pm.shift(-HORIZON_H).rename("y")


def build_features(df: pd.DataFrame, target: str = "t24",
                   with_future_weather: bool = False) -> tuple[pd.DataFrame, pd.Series]:
    """Build the feature table X and target y.

    Past features use data at time <= t only. With with_future_weather=True, next-24 h weather
    columns are added (see future_weather). df needs an hourly UTC DatetimeIndex and columns
    pm25, temp, rh, wind_speed, wind_dir, precip. Rows with NaN are kept; the caller drops them
    for training or picks the current-hour row for live use.
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
    if with_future_weather:
        X = X.join(future_weather(df))
    return X, make_target(pm, target)



# ---------- explanation, tips and live inference (SPEC §5.8–5.10) ----------
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_FIELDS = {
    "temperature_2m": "temp", "relative_humidity_2m": "rh", "wind_speed_10m": "wind_speed",
    "wind_direction_10m": "wind_dir", "precipitation": "precip",
}
CACHE_SECONDS = 30 * 60
_cache: dict[tuple, tuple[float, dict]] = {}

CATEGORY_HI = {
    "Good": "अच्छी", "Satisfactory": "संतोषजनक", "Moderately polluted": "मध्यम प्रदूषित",
    "Poor": "खराब", "Very poor": "बहुत खराब", "Severe": "गंभीर",
}
# feature group -> {direction: (english, hindi)}; "up" = pushes PM2.5 higher
PHRASES = {
    "pm25": {"up": ("recent PM2.5 has been high", "हाल में PM2.5 ज़्यादा रहा है"),
             "down": ("recent PM2.5 has been low", "हाल में PM2.5 कम रहा है")},
    "wind_speed": {"up": ("wind is weak", "हवा धीमी है"),
                   "down": ("wind is strong", "हवा तेज़ है")},
    "rh": {"up": ("humidity is high", "नमी ज़्यादा है"),
           "down": ("humidity is low", "नमी कम है")},
    "temp": {"up": ("it is cold", "ठंड है"),
             "down": ("it is warm", "मौसम गर्म है")},
    "season": {"up": ("it is the winter smog season", "सर्दियों में स्मॉग का मौसम है"),
               "down": ("it is not the smog season", "यह स्मॉग का मौसम नहीं है")},
    "precip": {"up": ("there has been no rain", "बारिश नहीं हुई है"),
               "down": ("recent rain has cleaned the air", "हाल की बारिश ने हवा साफ़ की है")},
    "wind_dir": {"up": ("the wind is coming from a polluted direction",
                        "हवा प्रदूषित दिशा से आ रही है"),
                 "down": ("the wind is coming from a cleaner direction",
                          "हवा साफ़ दिशा से आ रही है")},
    "time": {"up": ("the usual daily pattern pushes it up", "दिन का सामान्य पैटर्न इसे बढ़ाता है"),
             "down": ("the usual daily pattern keeps it down", "दिन का सामान्य पैटर्न इसे घटाता है")},
    # next-24 h weather forecast features
    "fc_wind_speed": {"up": ("weak wind is forecast", "धीमी हवा का पूर्वानुमान है"),
                      "down": ("strong wind is forecast", "तेज़ हवा का पूर्वानुमान है")},
    "fc_rh": {"up": ("high humidity is forecast", "ज़्यादा नमी का पूर्वानुमान है"),
              "down": ("low humidity is forecast", "कम नमी का पूर्वानुमान है")},
    "fc_temp": {"up": ("a cold day is forecast", "ठंडे दिन का पूर्वानुमान है"),
                "down": ("a warm day is forecast", "गर्म दिन का पूर्वानुमान है")},
    "fc_precip": {"up": ("no rain is forecast", "बारिश का पूर्वानुमान नहीं है"),
                  "down": ("rain is forecast", "बारिश का पूर्वानुमान है")},
    "fc_wind_dir": {"up": ("wind is forecast from a polluted direction", "प्रदूषित दिशा से हवा का पूर्वानुमान है"),
                    "down": ("wind is forecast from a cleaner direction", "साफ़ दिशा से हवा का पूर्वानुमान है")},
}
TIPS = {
    1: ("Good day to be outdoors. Keep windows open for fresh air.",
        "बाहर जाने के लिए अच्छा दिन है। ताज़ी हवा के लिए खिड़कियाँ खोलें।"),
    2: ("Sensitive people (asthma, elderly, children) should limit long outdoor exercise.",
        "संवेदनशील लोग (दमा, बुज़ुर्ग, बच्चे) बाहर लंबी कसरत कम करें।"),
    3: ("Avoid outdoor exercise. Wear a well-fitting N95 mask outside. Don't burn waste.",
        "बाहर कसरत न करें। बाहर अच्छा N95 मास्क पहनें। कचरा न जलाएँ।"),
    4: ("Stay indoors if possible, keep windows closed, use a purifier if you have one. "
        "Seek medical help for breathing trouble.",
        "हो सके तो घर में रहें, खिड़कियाँ बंद रखें, प्यूरीफ़ायर हो तो चलाएँ। "
        "साँस की तकलीफ़ हो तो डॉक्टर से मिलें।"),
}
DISCLAIMER = ("This is general awareness, not medical advice.",
              "यह सामान्य जानकारी है, चिकित्सा सलाह नहीं।")


def feature_group(name: str) -> str:
    """Map a feature name to its phrase group."""
    if name.startswith("fut_"):
        for key in ("wind_speed", "rh", "temp", "precip", "wind_dir"):
            if name.startswith(f"fut_{key}"):
                return f"fc_{key}"
    if name.startswith("pm25_"):
        return "pm25"
    if name in ("is_winter", "month"):
        return "season"
    if name == "precip_24h_sum":
        return "precip"
    if name.startswith("wind_dir"):
        return "wind_dir"
    if name in ("hour", "dow"):
        return "time"
    return name


def top_reasons(shap_row: np.ndarray, names: list[str], high: bool) -> list[str]:
    """Return the 2 distinct phrase groups that push the forecast up (high) or down (low)."""
    order = np.argsort(-shap_row if high else shap_row)
    groups: list[str] = []
    for i in order:
        group = feature_group(names[i])
        if group not in groups:
            groups.append(group)
        if len(groups) == 2:
            break
    return groups


def make_reason(category: str, groups: list[str], high: bool, lang: str) -> str:
    """Build the one-sentence reason in English or Hindi."""
    direction = "up" if high else "down"
    idx = 1 if lang == "hi" else 0
    parts = [PHRASES[g][direction][idx] for g in groups]
    if lang == "hi":
        return f"कल हवा {CATEGORY_HI[category]} रहने की संभावना है, मुख्य रूप से क्योंकि {' और '.join(parts)}।"
    return f"Tomorrow looks {category} mainly because {' and '.join(parts)}."


@lru_cache(maxsize=1)
def load_model() -> tuple[lgb.Booster, list[str], dict]:
    """Load the LightGBM booster, feature list and metrics once."""
    metrics = json.loads((MODELS_DIR / "metrics.json").read_text())
    # ponytail: live path supports LightGBM only; if a retrain ever picks "linear", add a linear explainer here
    if metrics["model"]["kind"] != "lightgbm":
        raise RuntimeError(f"live forecast supports LightGBM only, metrics.json says {metrics['model']['kind']}")
    booster = lgb.Booster(model_file=str(MODELS_DIR / "lgbm.txt"))
    features = json.loads((MODELS_DIR / "feature_list.json").read_text())
    return booster, features, metrics


def fetch_hourly(url: str, lat: float, lon: float, fields: dict) -> pd.DataFrame:
    """Fetch the last 3 days + next 2 days of hourly data from an Open-Meteo API (UTC index)."""
    resp = requests.get(url, params={
        "latitude": lat, "longitude": lon, "hourly": ",".join(fields),
        "past_days": 3, "forecast_days": 2, "timezone": "GMT",
    }, timeout=30)
    resp.raise_for_status()
    hourly = resp.json()["hourly"]
    df = pd.DataFrame({new: hourly[old] for old, new in fields.items()})
    df.index = pd.to_datetime(hourly["time"], utc=True)
    return df


def fetch_live(lat: float, lon: float) -> pd.DataFrame:
    """Last ~72 h of PM2.5 + weather, plus the weather FORECAST for the next hours.

    PM2.5 after the current hour is blanked: only past PM2.5 is ever used (same source as training).
    """
    air = fetch_hourly(AIR_URL, lat, lon, {"pm2_5": "pm25"})
    weather = fetch_hourly(WEATHER_URL, lat, lon, WEATHER_FIELDS)
    df = weather.join(air, how="left")
    now = pd.Timestamp.now(tz="UTC").floor("h")
    df.loc[df.index > now, "pm25"] = np.nan
    return df


def current_row(X: pd.DataFrame, live: pd.DataFrame) -> pd.DataFrame:
    """The latest hour that has a measured PM2.5 and every feature filled in."""
    ok = X.notna().all(axis=1) & live["pm25"].reindex(X.index).notna()
    return X[ok].iloc[[-1]]


def predict_core(lat: float, lon: float) -> dict:
    """Predict tomorrow's PM2.5 (next-24 h mean for the current model) and its SHAP reason groups."""
    booster, features, metrics = load_model()
    config = metrics["model"]
    live = fetch_live(lat, lon)
    X, _ = build_features(live, target=config["target"], with_future_weather=config["future_weather"])
    row = current_row(X[features], live)
    value = float(booster.predict(row)[0])
    # TreeSHAP values from LightGBM itself (what shap.TreeExplainer calls internally); last column = bias
    shap_row = booster.predict(row, pred_contrib=True)[0][:-1]
    category, tier, colour = pm25_to_category(value)
    high = tier >= 2
    return {
        "pm25_now": round(float(live.loc[row.index[0], "pm25"]), 1), "pm25_tomorrow": round(value, 1), "category": category,
        "tier": tier, "color": colour, "high": high,
        "groups": top_reasons(shap_row, features, high), "test_mae": metrics["lightgbm"]["mae"],
        "target": config["target_label"],
    }


def get_forecast(lat: float, lon: float, lang: str = "en") -> dict:
    """Full /forecast response, with the model result cached for 30 minutes per location."""
    key = (round(lat, 2), round(lon, 2))
    cached = _cache.get(key)
    if cached is None or time.time() - cached[0] > CACHE_SECONDS:
        cached = (time.time(), predict_core(lat, lon))
        _cache[key] = cached
    generated_at, core = cached
    idx = 1 if lang == "hi" else 0
    return {
        "location": {"lat": lat, "lon": lon},
        "generated_at": datetime.fromtimestamp(generated_at, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pm25_now": core["pm25_now"], "pm25_tomorrow": core["pm25_tomorrow"],
        "category": core["category"], "tier": core["tier"], "color": core["color"],
        "reason": make_reason(core["category"], core["groups"], core["high"], lang),
        "tip": TIPS[core["tier"]][idx], "disclaimer": DISCLAIMER[idx],
        "model": {"name": "lightgbm", "test_mae": core["test_mae"], "target": core["target"]},
    }
