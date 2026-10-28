"""Train persistence, linear and LightGBM forecasters (SPEC §5.3–5.6).

Writes models/lgbm.txt, models/feature_list.json, models/metrics.json and 4 plots in docs/evidence/.

Usage (from backend/):
    python scripts/train_forecast.py
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import lightgbm as lgb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, f1_score,  # noqa: E402
                             mean_absolute_error, mean_squared_error, r2_score)
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.forecast import CATEGORIES, build_features, pm25_to_category  # noqa: E402

DATA_PATH = BACKEND_DIR / "data" / "hourly.parquet"
MODELS_DIR = BACKEND_DIR / "models"
EVIDENCE_DIR = BACKEND_DIR.parent / "docs" / "evidence"
DATA_SOURCE = "openmeteo"
POOR_PLUS = {"Poor", "Very poor", "Severe"}


def time_split(X: pd.DataFrame, y: pd.Series) -> dict:
    """Split rows 70/15/15 in time order (never shuffled)."""
    n = len(X)
    a, b = int(n * 0.70), int(n * 0.85)
    return {"train": (X.iloc[:a], y.iloc[:a]), "val": (X.iloc[a:b], y.iloc[a:b]),
            "test": (X.iloc[b:], y.iloc[b:])}


def to_categories(values: np.ndarray) -> list[str]:
    """Convert PM2.5 values to CPCB category names."""
    return [pm25_to_category(v)[0] for v in values]


def regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    """MAE, RMSE and R² rounded to 3 decimals."""
    return {"mae": round(mean_absolute_error(y_true, y_pred), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3),
            "r2": round(r2_score(y_true, y_pred), 3)}


def category_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    """Category accuracy, macro-F1 and recall for Poor-or-worse."""
    true_cat, pred_cat = to_categories(y_true.values), to_categories(y_pred)
    true_bad = np.array([c in POOR_PLUS for c in true_cat])
    pred_bad = np.array([c in POOR_PLUS for c in pred_cat])
    return {"acc_cat": round(accuracy_score(true_cat, pred_cat), 3),
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


def save_plots(model: lgb.LGBMRegressor, X_test: pd.DataFrame, y_test: pd.Series,
               pred: np.ndarray) -> None:
    """Save pred_vs_actual, confusion_matrix, shap_summary and feature_importance plots."""
    last = y_test.index >= y_test.index.max() - pd.Timedelta(days=30)
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(y_test.index[last], y_test[last], label="actual (t+24h)", color="black", lw=1)
    ax.plot(y_test.index[last], pred[last], label="LightGBM", color="#4C9A2A", lw=1)
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("Predicted vs actual PM2.5, last 30 days of test set")
    ax.legend()
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "pred_vs_actual.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 7))
    ConfusionMatrixDisplay.from_predictions(to_categories(y_test.values), to_categories(pred),
                                            labels=CATEGORIES, ax=ax, colorbar=False,
                                            xticks_rotation=45)
    ax.set_title("LightGBM CPCB category confusion matrix (test)")
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "confusion_matrix.png", dpi=120)
    plt.close(fig)

    sample = X_test.sample(min(2000, len(X_test)), random_state=42)
    shap_values = shap.TreeExplainer(model.booster_).shap_values(sample)
    shap.summary_plot(shap_values, sample, show=False)
    plt.tight_layout()
    plt.savefig(EVIDENCE_DIR / "shap_summary.png", dpi=120)
    plt.close("all")

    gain = pd.Series(model.booster_.feature_importance("gain"), index=X_test.columns).sort_values()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(gain.index, gain.values, color="#4C9A2A")
    ax.set_xlabel("Total gain")
    ax.set_title("LightGBM feature importance (gain)")
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "feature_importance.png", dpi=120)
    plt.close(fig)


def main() -> None:
    """Train all three models, print the metric table, and save model + metrics + plots."""
    df = pd.read_parquet(DATA_PATH)
    X, y = build_features(df)
    keep = X.notna().all(axis=1) & y.notna()
    X, y = X[keep], y[keep]
    split = time_split(X, y)
    X_test, y_test = split["test"]
    pm25_now = df["pm25"].reindex(X_test.index)

    linear = make_pipeline(StandardScaler(), LinearRegression()).fit(*split["train"])
    model = train_lightgbm(split)
    preds = {"persistence": pm25_now.values, "linear": linear.predict(X_test),
             "lightgbm": model.predict(X_test, num_iteration=model.best_iteration_)}

    metrics = {"data_source": DATA_SOURCE, "rows": len(X),
               "test_period": [str(X_test.index.min().date()), str(X_test.index.max().date())],
               "best_iteration": int(model.best_iteration_)}
    for name, pred in preds.items():
        metrics[name] = {**regression_metrics(y_test, pred), **category_metrics(y_test, pred)}

    MODELS_DIR.mkdir(exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(MODELS_DIR / "lgbm.txt"), num_iteration=model.best_iteration_)
    (MODELS_DIR / "feature_list.json").write_text(json.dumps(list(X.columns), indent=2))
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    save_plots(model, X_test, y_test, preds["lightgbm"])

    print(f"rows: {len(X)}  train/val/test: {[len(v[0]) for v in split.values()]}")
    print(f"test period: {metrics['test_period']}  best iteration: {metrics['best_iteration']}")
    table = pd.DataFrame({name: metrics[name] for name in preds}).T
    print(table.to_string())
    print(f"\nsaved models/lgbm.txt, feature_list.json, metrics.json and 4 plots in {EVIDENCE_DIR}")


if __name__ == "__main__":
    main()
