"""Tests for forecast features and CPCB categories (SPEC §12)."""
import numpy as np
import pandas as pd
import pytest

from app.forecast import build_features, pm25_to_category


def make_hourly(hours: int = 200) -> pd.DataFrame:
    """Random hourly weather + PM2.5 table with a UTC index."""
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=hours, freq="h", tz="UTC")
    return pd.DataFrame({
        "pm25": rng.uniform(10, 300, hours), "temp": rng.uniform(5, 40, hours),
        "rh": rng.uniform(20, 100, hours), "wind_speed": rng.uniform(0, 20, hours),
        "wind_dir": rng.uniform(0, 360, hours), "precip": rng.uniform(0, 2, hours),
    }, index=idx)


def test_build_features_uses_no_future_data() -> None:
    """Changing data after time t must not change the features at time t."""
    df = make_hourly()
    t = 120
    X_before, _ = build_features(df)
    changed = df.copy()
    changed.iloc[t + 1:] = changed.iloc[t + 1:] * 5 + 100
    X_after, _ = build_features(changed)
    pd.testing.assert_frame_equal(X_before.iloc[:t + 1], X_after.iloc[:t + 1])


def test_target_is_pm25_24h_ahead() -> None:
    """y at row t equals pm25 at row t+24."""
    df = make_hourly()
    _, y = build_features(df)
    assert y.iloc[10] == df["pm25"].iloc[34]
    assert y.iloc[-24:].isna().all()


@pytest.mark.parametrize("value, category", [
    (30, "Good"), (31, "Satisfactory"), (60, "Satisfactory"), (61, "Moderately polluted"),
    (90, "Moderately polluted"), (91, "Poor"), (120, "Poor"), (121, "Very poor"),
    (250, "Very poor"), (251, "Severe"),
])
def test_category_band_edges(value: float, category: str) -> None:
    """CPCB band edges map to the right category."""
    assert pm25_to_category(value)[0] == category


def test_mean24_target_is_mean_of_next_24_hours() -> None:
    """y at row t equals the mean of pm25 over rows t+1 .. t+24."""
    df = make_hourly()
    _, y = build_features(df, target="mean24")
    assert abs(y.iloc[10] - df["pm25"].iloc[11:35].mean()) < 1e-9
    assert y.iloc[-24:].isna().all()


def test_future_weather_never_uses_future_pm25() -> None:
    """With next-24h weather features, changing FUTURE PM2.5 still leaves features at t unchanged."""
    df = make_hourly()
    t = 120
    X_before, _ = build_features(df, with_future_weather=True)
    changed = df.copy()
    changed.iloc[t + 1:, changed.columns.get_loc("pm25")] += 500
    X_after, _ = build_features(changed, with_future_weather=True)
    pd.testing.assert_frame_equal(X_before.iloc[:t + 1], X_after.iloc[:t + 1])


def test_future_weather_is_next_24h_mean() -> None:
    """fut_temp_mean24 at t is the mean temperature over t+1 .. t+24."""
    df = make_hourly()
    X, _ = build_features(df, with_future_weather=True)
    assert abs(X["fut_temp_mean24"].iloc[10] - df["temp"].iloc[11:35].mean()) < 1e-9
