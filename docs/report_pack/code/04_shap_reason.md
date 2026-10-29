# SHAP reason sentence (EN/HI)

Source: `backend/app/forecast.py` (40 lines in total), copied unchanged.

Lines 163–202:

```python
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
```
