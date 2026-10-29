"""Print-ready report figures (300 dpi PNG, readable in black and white) -> docs/report_pack/figures/.

Uses only real files: data/hourly.parquet, models/ (v2 LightGBM + metrics.json), and the two sample
photos in docs/report_pack/raw/samples/. The v2 test predictions are recomputed and checked against
metrics.json before anything is drawn.

Usage (from backend/):
    python scripts/report_figures.py
"""
import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.dates

matplotlib.use("Agg")
import lightgbm as lgb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from sklearn.metrics import ConfusionMatrixDisplay, mean_absolute_error  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.forecast import BANDS, CATEGORIES, build_features, pm25_to_category  # noqa: E402
from app.verify import LITTER, detect  # noqa: E402
from scripts.train_forecast import shared_rows, time_split  # noqa: E402

PACK = BACKEND_DIR.parent / "docs" / "report_pack"
FIG = PACK / "figures"
SAMPLES = PACK / "raw" / "samples"
MODELS = BACKEND_DIR / "models"
DPI = 300
UNIT = "PM2.5 (µg/m³)"
# light grey -> black: low values stay visible on a white page
GREY = LinearSegmentedColormap.from_list("grey", ["#d9d9d9", "#000000"])

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "axes.edgecolor": "black",
    "axes.grid": True, "grid.color": "#bfbfbf", "grid.linestyle": ":", "grid.linewidth": 0.6,
    "lines.linewidth": 1.4,
})


def save(fig: plt.Figure, name: str) -> None:
    """Save a figure as a 300 dpi PNG and close it."""
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=DPI)
    plt.close(fig)
    print("saved", name)


def ist(df: pd.DataFrame) -> pd.DataFrame:
    """Same table with the index in India time (IST)."""
    out = df.copy()
    out.index = out.index.tz_convert("Asia/Kolkata")
    return out


# ---------------- EDA ----------------
def eda_figures(df: pd.DataFrame) -> None:
    """Monthly mean, hour-of-day mean, PM2.5 vs wind, and a greyscale correlation heatmap."""
    local = ist(df)
    monthly = local.groupby(local.index.month)["pm25"].mean()
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.bar(monthly.index, monthly.values, color="#8c8c8c", edgecolor="black", hatch="//")
    ax.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_xlabel("Month")
    ax.set_ylabel(f"Mean {UNIT}")
    ax.set_title("Monthly mean PM2.5 (Aug 2022 – Oct 2026)")
    ax.grid(axis="x", visible=False)
    save(fig, "eda_01_monthly_mean_pm25.png")

    hourly = local.groupby(local.index.hour)["pm25"].mean()
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.plot(hourly.index, hourly.values, color="black", marker="o", markersize=4)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hour of day (IST, h)")
    ax.set_ylabel(f"Mean {UNIT}")
    ax.set_title("Mean PM2.5 by hour of day")
    save(fig, "eda_02_pm25_by_hour.png")

    sample = df.sample(min(5000, len(df)), random_state=42)
    bins = pd.cut(df["wind_speed"], bins=np.arange(0, df["wind_speed"].max() + 2, 2))
    trend = df.groupby(bins, observed=True)["pm25"].agg(["mean", "count"])
    trend = trend[trend["count"] >= 30]  # skip bins with too few hours to be meaningful
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.scatter(sample["wind_speed"], sample["pm25"], s=3, color="#7f7f7f", alpha=0.35,
               label="hourly values (random 5,000)")
    ax.plot([b.mid for b in trend.index], trend["mean"], color="black", marker="s", markersize=4,
            label="mean per 2 km/h bin (≥30 h)")
    ax.set_xlabel("Wind speed at 10 m (km/h)")
    ax.set_ylabel(UNIT)
    ax.set_title("PM2.5 vs wind speed")
    ax.legend(loc="upper right")
    save(fig, "eda_03_pm25_vs_wind.png")

    cols = ["pm25", "pm10", "no2", "o3", "co", "so2", "temp", "rh", "wind_speed", "wind_dir", "precip"]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(6.5, 5.6))
    im = ax.imshow(corr, cmap="Greys", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)), cols, rotation=45, ha="right")
    ax.set_yticks(range(len(cols)), cols)
    ax.grid(False)
    for i in range(len(cols)):
        for j in range(len(cols)):
            v = corr.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if v > 0.45 else "black")
    fig.colorbar(im, ax=ax, label="Pearson correlation (–1 white … +1 black)")
    ax.set_title("Correlation of pollutants and weather (hourly)")
    save(fig, "eda_04_correlation_heatmap.png")


# ---------------- model ----------------
def test_predictions(df: pd.DataFrame, metrics: dict) -> tuple[pd.DataFrame, pd.Series, np.ndarray, lgb.Booster]:
    """Rebuild the v2 test set exactly as in training and predict it with the saved model."""
    cfg = metrics["model"]
    features = json.loads((MODELS / "feature_list.json").read_text())
    booster = lgb.Booster(model_file=str(MODELS / "lgbm.txt"))
    rows = shared_rows(df)
    X, y = build_features(df, target=cfg["target"], with_future_weather=cfg["future_weather"])
    X_test, y_test = time_split(X.loc[rows, features], y.loc[rows])["test"]
    pred = booster.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    assert abs(mae - metrics["lightgbm"]["mae"]) < 0.01, f"MAE {mae:.3f} != metrics.json"
    print(f"v2 test MAE recomputed: {mae:.3f} (metrics.json {metrics['lightgbm']['mae']})")
    return X_test, y_test, pred, booster


def model_figures(df: pd.DataFrame, metrics: dict) -> None:
    """Predicted vs actual, residuals, MAE bars, importance, SHAP, confusion matrix, one month."""
    X_test, y_test, pred, booster = test_predictions(df, metrics)
    label = metrics["model"]["target_label"]

    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    ax.scatter(y_test, pred, s=3, color="black", alpha=0.25, label="test hours")
    hi = float(max(y_test.max(), pred.max())) * 1.05
    ax.plot([0, hi], [0, hi], color="black", linestyle="--", linewidth=1.2, label="perfect forecast (y = x)")
    ax.set_xlim(0, hi)
    ax.set_ylim(0, hi)
    ax.set_xlabel(f"Actual {label} (µg/m³)")
    ax.set_ylabel("LightGBM forecast (µg/m³)")
    ax.set_title(f"Predicted vs actual, test set (n = {len(y_test):,})")
    ax.legend(loc="upper left")
    save(fig, "model_01_predicted_vs_actual.png")

    resid = pred - y_test.values
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.hist(resid, bins=60, color="#a6a6a6", edgecolor="black", linewidth=0.4)
    ax.axvline(0, color="black", linestyle="--", linewidth=1.2, label="zero error")
    ax.axvline(resid.mean(), color="black", linestyle=":", linewidth=1.6,
               label=f"mean error {resid.mean():+.1f} µg/m³")
    ax.set_xlabel("Forecast error = forecast − actual (µg/m³)")
    ax.set_ylabel("Number of test hours")
    ax.set_title("Residuals of the LightGBM forecast (test set)")
    ax.legend()
    save(fig, "model_02_residual_histogram.png")

    exp = {(e["target"], e["future_weather"]): e for e in metrics["experiments"]}
    v1, v2 = exp[("t24", False)]["test"], exp[("mean24", True)]["test"]
    names = [("persistence", "Persistence"), ("linear", "Linear regression"), ("lightgbm", "LightGBM")]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for offset, scores, hatch, fill, tag in [(-0.2, v1, "//", "white", "v1: PM2.5 at t+24 h, past features"),
                                             (0.2, v2, "", "#595959", "v2: next-24 h mean, + weather")]:
        bars = ax.bar(x + offset, [scores[k]["mae"] for k, _ in names], width=0.4, color=fill,
                      edgecolor="black", hatch=hatch, label=tag)
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
    ax.set_xticks(x, [n for _, n in names])
    ax.set_ylabel("Test MAE (µg/m³)")
    ax.set_title("Forecast error by model, v1 vs v2 (lower is better)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, max(v1[k]["mae"] for k, _ in names) * 1.2)
    save(fig, "model_03_mae_comparison_v1_v2.png")

    gain = pd.Series(booster.feature_importance("gain"), index=X_test.columns)
    gain = (gain / gain.sum() * 100).sort_values()
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    ax.barh(gain.index, gain.values, color="#595959", edgecolor="black")
    ax.set_xlabel("Share of total split gain (%)")
    ax.set_title("LightGBM feature importance (v2)")
    ax.grid(axis="y", visible=False)
    save(fig, "model_04_feature_importance.png")

    sample = X_test.sample(min(2000, len(X_test)), random_state=42)
    values = shap.TreeExplainer(booster).shap_values(sample)
    shap.summary_plot(values, sample, cmap=GREY, show=False, max_display=15, plot_size=(6.5, 6.0))
    fig = plt.gcf()
    fig.axes[0].set_xlabel("SHAP value: effect on forecast (µg/m³)")
    fig.axes[0].set_title("SHAP summary (v2 LightGBM), 2,000 random test hours\n"
                          "Dark dot = high feature value; right of 0 = pushes forecast up", fontsize=9)
    save(fig, "model_05_shap_summary.png")

    fig, ax = plt.subplots(figsize=(6.5, 5.8))
    true_cat = [pm25_to_category(v)[0] for v in y_test.values]
    pred_cat = [pm25_to_category(v)[0] for v in pred]
    ConfusionMatrixDisplay.from_predictions(true_cat, pred_cat, labels=CATEGORIES, cmap="Greys",
                                            ax=ax, colorbar=False)
    short = [c.replace("Moderately polluted", "Moderately\npolluted").replace("Very poor", "Very\npoor")
             for c in CATEGORIES]
    ax.set_xticks(range(len(CATEGORIES)), short, fontsize=8)
    ax.set_yticks(range(len(CATEGORIES)), short, fontsize=8)
    ax.grid(False)
    ax.set_xlabel("Forecast CPCB category")
    ax.set_ylabel("Actual CPCB category")
    ax.set_title("CPCB category confusion matrix, test set (counts of hours)")
    save(fig, "model_06_confusion_matrix.png")

    month = y_test.index >= y_test.index.max() - pd.Timedelta(days=30)
    t = y_test.index[month].tz_convert("Asia/Kolkata")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(t, y_test[month].values, color="black", linewidth=1.3, label=f"actual ({label})")
    ax.plot(t, pred[month], color="#595959", linestyle="--", linewidth=1.3, label="LightGBM forecast")
    lo, hi = ax.get_ylim()
    for upper, name, _, _ in BANDS[:5]:  # CPCB band edges inside the plotted range, labelled outside
        if lo < upper < hi:
            ax.axhline(upper, color="#808080", linestyle=(0, (1, 3)), linewidth=0.8)
            ax.text(1.01, upper, f"{name}\n≤ {upper}", transform=ax.get_yaxis_transform(),
                    fontsize=6.5, color="#404040", va="center")
    ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=4, tz=t.tz))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b", tz=t.tz))
    ax.set_xlabel("Date (IST)")
    ax.set_ylabel(UNIT)
    ax.set_title(f"One month of the test set: {t[0]:%d %b} – {t[-1]:%d %b %Y} (dotted lines = CPCB band edges)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8, frameon=False)
    save(fig, "timeseries_01_one_month_actual_vs_forecast.png")


# ---------------- verification ----------------
def draw_detections(path: Path, action_key: set[str], title: str, out_name: str) -> None:
    """Run YOLOv8n on a photo and draw every box in black/white; key classes get thick boxes."""
    image = Image.open(path).convert("RGB")
    dets = detect(image)
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    big = ImageFont.load_default(size=max(14, image.width // 36))
    small = ImageFont.load_default(size=max(10, image.width // 60))
    for d in sorted(dets, key=lambda d: d["name"] in action_key):  # key classes drawn last (on top)
        x1, y1, x2, y2 = d["box"]
        key = d["name"] in action_key
        draw.rectangle([x1, y1, x2, y2], outline="white", width=8 if key else 3)
        draw.rectangle([x1, y1, x2, y2], outline="black", width=5 if key else 1)
        font = big if key else small
        text = f"USED: {d['name']} {d['conf']:.2f}" if key else f"{d['name']} {d['conf']:.2f}"
        tw, th = draw.textbbox((0, 0), text, font=font)[2:]
        ty = max(0, y1 - th - 4)
        draw.rectangle([x1, ty, x1 + tw + 6, ty + th + 4], fill="black")
        draw.text((x1 + 3, ty + 1), text, fill="white", font=font)
    fig, ax = plt.subplots(figsize=(6.5, 6.5 * image.height / image.width + 0.6))
    ax.imshow(canvas)
    ax.axis("off")
    summary = ", ".join(f"{d['name']} {d['conf']:.2f}" for d in dets if d["name"] in action_key) or "none"
    ax.set_title(f"{title}\nYOLOv8n detections: {len(dets)}; used for the check: {summary}", fontsize=9)
    save(fig, out_name)


def main() -> None:
    """Make every report figure."""
    FIG.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(BACKEND_DIR / "data" / "hourly.parquet").asfreq("h")
    metrics = json.loads((MODELS / "metrics.json").read_text())
    eda_figures(df)
    model_figures(df, metrics)
    draw_detections(SAMPLES / "coco_139_plant.jpg", {"potted plant"},
                    "Plant photo (COCO val2017 #139) submitted as 'sapling' → needs_review (0.421)",
                    "verify_01_yolo_plant.png")
    draw_detections(SAMPLES / "synthetic_wall.jpg", {"potted plant"} | set(LITTER),
                    "Plain wall (generated texture) submitted as 'sapling' → rejected",
                    "verify_02_yolo_wall.png")


if __name__ == "__main__":
    main()
