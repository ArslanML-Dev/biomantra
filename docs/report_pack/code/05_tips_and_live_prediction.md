# Health tips, disclaimer and live SHAP prediction

Source: `backend/app/forecast.py` (37 lines in total), copied unchanged.

Lines 147–160:

```python
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
```

Lines 243–265:

```python
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
    shap_row = shap.TreeExplainer(booster).shap_values(row)[0]
    category, tier, colour = pm25_to_category(value)
    high = tier >= 2
    return {
        "pm25_now": round(float(live.loc[row.index[0], "pm25"]), 1), "pm25_tomorrow": round(value, 1), "category": category,
        "tier": tier, "color": colour, "high": high,
        "groups": top_reasons(shap_row, features, high), "test_mae": metrics["lightgbm"]["mae"],
        "target": config["target_label"],
    }
```
