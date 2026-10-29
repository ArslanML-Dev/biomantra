# CPCB bands and pm25_to_category

Source: `backend/app/forecast.py` (22 lines in total), copied unchanged.

Lines 14–35:

```python
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
```
