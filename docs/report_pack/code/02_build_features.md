# Feature building (past features, next-24 h weather, targets)

Source: `backend/app/forecast.py` (59 lines in total), copied unchanged.

Lines 38–96:

```python
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
```
