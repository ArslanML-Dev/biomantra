"""Tests for the hourly dataset gap filling (SPEC §4.3)."""
import numpy as np
import pandas as pd

from scripts.make_dataset import fill_short_gaps


def test_fills_short_gaps_and_keeps_long_gaps() -> None:
    """A 3 h gap is interpolated; a 4 h gap stays NaN."""
    idx = pd.date_range("2024-01-01", periods=12, freq="h", tz="UTC")
    values = [0, np.nan, np.nan, np.nan, 4, 5, np.nan, np.nan, np.nan, np.nan, 10, 11]
    filled = fill_short_gaps(pd.Series(values, index=idx, dtype=float))
    assert filled.iloc[1:4].tolist() == [1.0, 2.0, 3.0]
    assert filled.iloc[6:10].isna().all()
