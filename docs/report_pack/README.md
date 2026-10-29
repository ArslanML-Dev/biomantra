# Bio Mantra: report pack

Everything here comes from real files and real runs (2026-10-29). Nothing was estimated or drawn by hand.

- **Figures:** regenerate with `cd backend; python scripts/report_figures.py`. The script recomputes the v2 test predictions and stops if their MAE doesn't match `metrics.json`.
- **Screenshots:** regenerate with `cd frontend; node scripts/screenshots.mjs ../docs/evidence/screens` (needs the backend and the website running).
- **What isn't here:** see [MISSING.md](MISSING.md).

All figures are 300 dpi PNGs on a white background. They use only black and greys, with hatching, dashed and dotted lines or markers instead of colour, so they print correctly in black and white.

## figures/

| File | Shows | Source | Suggested caption |
|---|---|---|---|
| `eda_01_monthly_mean_pm25.png` | Mean PM2.5 per calendar month | `backend/data/hourly.parquet` (Open-Meteo, 2022-08-04 → 2026-10-26) | Seasonality: winter months (Nov–Jan) have about 2.5× the PM2.5 of the monsoon months. |
| `eda_02_pm25_by_hour.png` | Mean PM2.5 by hour of day (IST) | same | Daily cycle: the peak is around 22:00 IST and the low around 15:00 IST. |
| `eda_03_pm25_vs_wind.png` | Hourly PM2.5 vs wind speed, with binned means | same | PM2.5 falls as wind speed rises (bins with ≥30 hours). |
| `eda_04_correlation_heatmap.png` | Pearson correlations of pollutants and weather | same | PM2.5 correlates with PM10 and CO (+0.59) and with temperature (−0.38). |
| `model_01_predicted_vs_actual.png` | v2 LightGBM forecast vs actual, every test hour | `models/lgbm.txt`, test split 2026-03-08 → 2026-10-25 (n = 5,552) | Points near the dashed line are good forecasts. High values are under-forecast. |
| `model_02_residual_histogram.png` | Forecast − actual, test set | same | Distribution of forecast errors (µg/m³), with the mean error marked. |
| `model_03_mae_comparison_v1_v2.png` | Test MAE of persistence / linear / LightGBM, v1 and v2 | `raw/metrics_v2.json` → `experiments` | v1 = PM2.5 at t+24 h with past features; v2 = next-24 h mean with next-24 h weather. MAEs of different targets aren't directly comparable; see `raw/model_experiments.md`. |
| `model_04_feature_importance.png` | LightGBM gain importance (% of total) | `models/lgbm.txt` | Recent PM2.5 averages dominate; next-24 h wind and temperature are the most useful weather inputs. |
| `model_05_shap_summary.png` | SHAP beeswarm for 2,000 random test hours | `models/lgbm.txt` + SHAP TreeExplainer | How each feature pushes the forecast up or down. Dark dots = high feature values. |
| `model_06_confusion_matrix.png` | Actual vs forecast CPCB category (counts of test hours) | test split | Most errors are one category off. "Severe" is never forecast (only 26 test hours were Severe). |
| `timeseries_01_one_month_actual_vs_forecast.png` | Last 30 days of the test set, actual vs forecast | test split | Actual next-24 h mean (solid) vs LightGBM forecast (dashed), with the CPCB band edges dotted. |
| `verify_01_yolo_plant.png` | YOLOv8n boxes on the plant photo | `raw/samples/coco_139_plant.jpg` (COCO val2017 #139, CC BY 4.0) | Only "potted plant" (0.42) counts for a sapling. 0.42 is between 0.30 and 0.60, so the action goes to human review. |
| `verify_02_yolo_wall.png` | YOLOv8n on the plain wall image | `raw/samples/synthetic_wall.jpg` (generated texture, not a real photo) | No objects found → confidence 0 → rejected. |

Key numbers (from `raw/metrics_v2.json`), test set:
- v2 LightGBM: MAE 18.07, RMSE 26.30, R² 0.682, category accuracy 0.559, macro-F1 0.478, recall for Poor or worse 0.771.
- Baselines: linear MAE 19.53, persistence MAE 24.33.
- v1 LightGBM: MAE 30.02, accuracy 0.399, recall for Poor or worse 0.681.

## screenshots/

These are headless-Chromium (Playwright) captures of the website at **phone size (390×844)** and **laptop size (1366×768)**. They show `phone_*` and `laptop_*` for the user picker, Home EN/HI, Act (website message), Leaderboard (both tabs), Map, Admin login, Admin queue, About and Settings. `*_full.png` are full-length versions of the long pages.

The data behind them is a **separate demo database**. It holds one real submission (the COCO plant photo → needs_review 0.421), plus 10 approved sample actions and 2 hotspots that were inserted directly for display. The forecast on Home and Map is the live v2 forecast at capture time. These aren't photos of the Android app on a real phone; see MISSING.md.

## raw/

| File | What it is |
|---|---|
| `state.txt` | `git status`, `pytest -q` (35 passed), `git log --oneline -30` |
| `api_check.txt` | `start_demo.ps1 -Fresh` run: real responses of /health, /forecast (en, hi), /meta, /leaderboard, all HTTP 200 |
| `pytest_v_full.txt` | Full `pytest -v` output (35 passed) |
| `api_check_actions.txt` | Real responses of POST /actions, /admin/review, /leaderboard, /hotspots, /uploads |
| `api_check_hotspots.txt` | Real hotspot lifecycle: dumping report → admin approve → open hotspot → cleanup about 55 m away → closed |
| `metrics_v2.json`, `metrics_v1.json`, `feature_list_v2.json` | Model metrics (deployed v2, original v1) and v2 feature list |
| `model_experiments.md` | Full 4-configuration × 3-model results table and interpretation |
| `test_results.md` | Fraud test: 5 real results, 3 PENDING |
| `eda_notes.md`, `ai_check_samples.md`, `api_check_d1.md`, `demo_rehearsal.md`, `changes_from_synopsis.md` | Earlier evidence notes |
| `samples/` | Input photos: COCO #139 (plant), generated wall (verification figures), COCO #4134 and #285 (hotspot run). COCO images are CC BY 4.0 |

## diagrams/

There are 7 Mermaid sources with a black-and-white theme: architecture, data pipeline, verification flowchart, use cases, ER diagram, submit-action sequence and deployment. All 7 were checked by parsing and rendering them with Mermaid 11.4.1 in headless Chromium.

**No PNGs are included, because `mmdc` (mermaid-cli) isn't installed.** To render: `npx -p @mermaid-js/mermaid-cli mmdc -i diagrams/01_system_architecture.mmd -o 01.png -s 3 -b white`, or paste the file into mermaid.live.

## data/

- `metrics_v2.json` (the deployed model), `metrics_v1.json` (the original model) and `feature_list.json` (the v2 features).
- `eda_notes.md`.
- `dataset_summary.md`: source, date ranges, row counts, % missing before/after filling, `describe()` for pm25/temp/rh/wind_speed, and the split dates and sizes. It's generated by `backend/scripts/dataset_summary.py`.

## code/

11 excerpts, each copied unchanged from the source file by `backend/scripts/code_excerpts.py`, with the file path and line numbers at the top. Each has 22–59 lines, except `11_capacitor_config.md`, which is the whole 15-line file.

## docs/

`tech_stack.md`, `api.md` (every endpoint with real responses), `db_schema.md`, `testing.md` (full pytest output, what each test checks, the fraud table), `implementation_story.md`, `changes_from_synopsis.md`, `limitations.md`.
