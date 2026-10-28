"""Train and compare forecasters (SPEC §5.3–5.6 + model experiment).

Grid: target {t24 = PM2.5 at t+24 h, mean24 = mean PM2.5 over the next 24 h}
    x features {past only, past + next-24 h weather} x models {persistence, linear, LightGBM}.
All runs use the same rows and the same 70/15/15 time-ordered split.

Selection rule (fixed before looking at results): target mean24, because CPCB categories are
defined on 24-hour averages; then the feature set + model with the lowest VALIDATION MAE.
The test set is only used for reporting.

Writes models/ (chosen model, feature_list.json, metrics.json), 4 plots in docs/evidence/ and
docs/evidence/model_experiments.md.

Usage (from backend/):
    python scripts/train_forecast.py
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import joblib  # noqa: E402
import lightgbm as lgb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, f1_score,  # noqa: E402
                             mean_absolute_error, mean_squared_error, r2_score)
from sklearn.pipeline import Pipeline, make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.forecast import CATEGORIES, build_features, pm25_to_category  # noqa: E402

DATA_PATH = BACKEND_DIR / "data" / "hourly.parquet"
MODELS_DIR = BACKEND_DIR / "models"
EVIDENCE_DIR = BACKEND_DIR.parent / "docs" / "evidence"
DATA_SOURCE = "openmeteo"
POOR_PLUS = {"Poor", "Very poor", "Severe"}
TARGET_LABELS = {"t24": "PM2.5 at t+24 h", "mean24": "mean PM2.5 over the next 24 h"}
CONFIGS = [(target, fw) for target in ("t24", "mean24") for fw in (False, True)]
CHOSEN_TARGET = "mean24"


def time_split(X: pd.DataFrame, y: pd.Series) -> dict:
    """Split rows 70/15/15 in time order (never shuffled)."""
    n = len(X)
    a, b = int(n * 0.70), int(n * 0.85)
    return {"train": (X.iloc[:a], y.iloc[:a]), "val": (X.iloc[a:b], y.iloc[a:b]),
            "test": (X.iloc[b:], y.iloc[b:])}


def to_categories(values: np.ndarray) -> list[str]:
    """Convert PM2.5 values to CPCB category names."""
    return [pm25_to_category(v)[0] for v in values]


def scores(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    """MAE, RMSE, R², category accuracy, macro-F1 and recall for Poor-or-worse."""
    true_cat, pred_cat = to_categories(y_true.values), to_categories(y_pred)
    true_bad = np.array([c in POOR_PLUS for c in true_cat])
    pred_bad = np.array([c in POOR_PLUS for c in pred_cat])
    return {"mae": round(mean_absolute_error(y_true, y_pred), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3),
            "r2": round(r2_score(y_true, y_pred), 3),
            "acc_cat": round(accuracy_score(true_cat, pred_cat), 3),
            "macro_f1": round(f1_score(true_cat, pred_cat, average="macro", labels=CATEGORIES,
                                       zero_division=0), 3),
            "recall_poor_plus": round(float(pred_bad[true_bad].mean()), 3)}


def train_lightgbm(split: dict) -> lgb.LGBMRegressor:
    """Fit LightGBM with early stopping on the validation set."""
    model = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=31,
                              random_state=42, verbose=-1)
    model.fit(*split["train"], eval_set=[split["val"]],
              callbacks=[lgb.early_stopping(100, verbose=False)])
    return model


def run_config(df: pd.DataFrame, rows: pd.Index, target: str, fw: bool) -> dict:
    """Train persistence, linear and LightGBM for one (target, feature set) on the shared rows."""
    X, y = build_features(df, target=target, with_future_weather=fw)
    split = time_split(X.loc[rows], y.loc[rows])
    (X_val, y_val), (X_test, y_test) = split["val"], split["test"]
    linear = make_pipeline(StandardScaler(), LinearRegression()).fit(*split["train"])
    lgbm = train_lightgbm(split)
    models = {"linear": linear, "lightgbm": lgbm}
    pm_now = df["pm25"]
    result = {"target": target, "future_weather": fw, "split": split, "models": models,
              "val_mae": {}, "test": {}, "test_pred": {}}
    result["test_pred"]["persistence"] = pm_now.reindex(X_test.index).values
    result["val_mae"]["persistence"] = round(mean_absolute_error(y_val, pm_now.reindex(X_val.index)), 3)
    for name, model in models.items():
        result["val_mae"][name] = round(mean_absolute_error(y_val, model.predict(X_val)), 3)
        result["test_pred"][name] = model.predict(X_test)
    for name, pred in result["test_pred"].items():
        result["test"][name] = scores(y_test, pred)
    return result


def explain_plots(kind: str, model, X_test: pd.DataFrame) -> None:
    """SHAP summary + importance plots (LightGBM) or coefficient plots (linear)."""
    if kind == "lightgbm":
        sample = X_test.sample(min(2000, len(X_test)), random_state=42)
        shap.summary_plot(shap.TreeExplainer(model.booster_).shap_values(sample), sample, show=False)
        importance = pd.Series(model.booster_.feature_importance("gain"), index=X_test.columns)
        xlabel, title = "Total gain", "LightGBM feature importance (gain)"
    else:
        scaled = model[0].transform(X_test.sample(min(2000, len(X_test)), random_state=42))
        contrib = scaled * model[1].coef_
        shap.summary_plot(contrib, pd.DataFrame(scaled, columns=X_test.columns), show=False)
        importance = pd.Series(np.abs(model[1].coef_), index=X_test.columns)
        xlabel, title = "|coefficient| (standardised features)", "Linear model feature importance"
    plt.tight_layout()
    plt.savefig(EVIDENCE_DIR / "shap_summary.png", dpi=120)
    plt.close("all")
    importance = importance.sort_values()
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(importance.index, importance.values, color="#4C9A2A")
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "feature_importance.png", dpi=120)
    plt.close(fig)


def save_plots(kind: str, model, X_test: pd.DataFrame, y_test: pd.Series, pred: np.ndarray,
               label: str) -> None:
    """Save pred_vs_actual, confusion_matrix, shap_summary and feature_importance plots."""
    last = y_test.index >= y_test.index.max() - pd.Timedelta(days=30)
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(y_test.index[last], y_test[last], label=f"actual ({label})", color="black", lw=1)
    ax.plot(y_test.index[last], pred[last], label=kind, color="#4C9A2A", lw=1)
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("Predicted vs actual, last 30 days of test set")
    ax.legend()
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "pred_vs_actual.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 7))
    ConfusionMatrixDisplay.from_predictions(to_categories(y_test.values), to_categories(pred),
                                            labels=CATEGORIES, ax=ax, colorbar=False,
                                            xticks_rotation=45)
    ax.set_title(f"{kind} CPCB category confusion matrix (test)")
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "confusion_matrix.png", dpi=120)
    plt.close(fig)
    explain_plots(kind, model, X_test)


def config_name(target: str, fw: bool) -> str:
    """Short readable name of a (target, feature set) configuration."""
    return f"{target} + {'past & next-24h weather' if fw else 'past only'}"


def write_report(results: list[dict], chosen: dict, chosen_kind: str, rows: int, period: list) -> None:
    """Write docs/evidence/model_experiments.md with the real numbers."""
    lines = [
        "# Forecast model experiments",
        "",
        "Generated by `backend/scripts/train_forecast.py` (real numbers, re-run to reproduce).",
        f"Data: Open-Meteo hourly PM2.5 + weather, {rows:,} rows shared by every run; split 70/15/15 in time order; "
        f"test period {period[0]} → {period[1]}.",
        "",
        "**Targets.** `t24` = PM2.5 at exactly t+24 h (the original model). `mean24` = mean PM2.5 over t+1…t+24 h "
        "(new; matches the CPCB 24-hour averaging).",
        "",
        "**Next-24 h weather features (new).** Mean temperature, humidity, wind speed, wind direction (sin/cos) "
        "and total rain over t+1…t+24 h. In training these are the *actual* observed values, used as a stand-in "
        "for a weather forecast; at live inference `/forecast` takes them from the Open-Meteo weather forecast. "
        "Real forecasts have errors, so scores with these features are an **optimistic upper bound**. No future "
        "PM2.5 is ever used as a feature.",
        "",
        "**Selection rule (fixed before running).** Use target `mean24`; pick the feature set + model with the "
        "lowest **validation** MAE. Test scores are only reported.",
        "",
        "MAE values for `t24` and `mean24` measure different targets, so compare them within a target. "
        "Category metrics compare the forecast category with the true category of the same target.",
        "",
        "| Target | Features | Model | Val MAE | Test MAE | RMSE | R² | Cat. acc | Macro-F1 | Recall Poor+ |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        for name, s in r["test"].items():
            mark = " **← chosen**" if r is chosen and name == chosen_kind else ""
            old = " (original)" if r["target"] == "t24" and not r["future_weather"] and name == "lightgbm" else ""
            lines.append(f"| {r['target']} | {'past + next-24h weather' if r['future_weather'] else 'past only'} | "
                         f"{name}{old}{mark} | {r['val_mae'][name]} | {s['mae']} | {s['rmse']} | {s['r2']} | "
                         f"{s['acc_cat']} | {s['macro_f1']} | {s['recall_poor_plus']} |")
    lines += ["", f"**Chosen for `/forecast`:** {chosen_kind} on {config_name(chosen['target'], chosen['future_weather'])} "
              f"(lowest validation MAE among mean24 runs: {chosen['val_mae'][chosen_kind]})."]
    (EVIDENCE_DIR / "model_experiments.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Run the grid, choose the model by the rule above, and save model, metrics, plots and report."""
    df = pd.read_parquet(DATA_PATH).asfreq("h")
    keep = pd.Series(True, index=df.index)
    for target, fw in CONFIGS:  # rows valid for EVERY config, so all runs see the same data
        X, y = build_features(df, target=target, with_future_weather=fw)
        keep &= X.notna().all(axis=1) & y.notna()
    rows = df.index[keep]

    results = [run_config(df, rows, target, fw) for target, fw in CONFIGS]
    candidates = [(r["val_mae"][kind], i, kind) for i, r in enumerate(results)
                  if r["target"] == CHOSEN_TARGET for kind in ("linear", "lightgbm")]
    _, best_i, kind = min(candidates)
    chosen = results[best_i]
    model = chosen["models"][kind]
    X_test, y_test = chosen["split"]["test"]
    period = [str(X_test.index.min().date()), str(X_test.index.max().date())]

    MODELS_DIR.mkdir(exist_ok=True)
    for old in ("lgbm.txt", "linear.joblib"):
        (MODELS_DIR / old).unlink(missing_ok=True)
    if kind == "lightgbm":
        model.booster_.save_model(str(MODELS_DIR / "lgbm.txt"), num_iteration=model.best_iteration_)
    else:
        joblib.dump(model, MODELS_DIR / "linear.joblib")
    (MODELS_DIR / "feature_list.json").write_text(json.dumps(list(X_test.columns), indent=2))
    metrics = {
        "data_source": DATA_SOURCE, "rows": len(rows), "test_period": period,
        "model": {"kind": kind, "target": chosen["target"], "future_weather": chosen["future_weather"],
                  "target_label": TARGET_LABELS[chosen["target"]]},
        "best_iteration": int(chosen["models"]["lightgbm"].best_iteration_),
        **{name: chosen["test"][name] for name in ("persistence", "linear", "lightgbm")},
        "experiments": [{"target": r["target"], "future_weather": r["future_weather"],
                         "val_mae": r["val_mae"], "test": r["test"]} for r in results],
    }
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    save_plots(kind, model, X_test, y_test, chosen["test_pred"][kind], TARGET_LABELS[chosen["target"]])
    write_report(results, chosen, kind, len(rows), period)

    print(f"rows: {len(rows)}  test period: {period}")
    for r in results:
        print(f"\n== {config_name(r['target'], r['future_weather'])} ==")
        table = pd.DataFrame(r["test"]).T
        table.insert(0, "val_mae", pd.Series(r["val_mae"]))
        print(table.to_string())
    print(f"\nCHOSEN: {kind} on {config_name(chosen['target'], chosen['future_weather'])}")


if __name__ == "__main__":
    main()
