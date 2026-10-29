# Training: one configuration, and the main experiment loop

Source: `backend/scripts/train_forecast.py` (43 lines in total), copied unchanged.

Lines 211–253:

```python
def main() -> None:
    """Run the grid, choose the model by the rule above, and save model, metrics, plots and report."""
    df = pd.read_parquet(DATA_PATH).asfreq("h")
    rows = shared_rows(df)

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
```
