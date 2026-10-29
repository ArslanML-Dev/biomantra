# Testing

## 1. Automated tests (pytest)

Run with `cd backend; pytest -v`. YOLO is **mocked** in every test, so they never load the model. Each test uses its own temporary SQLite file.
Result: **35 passed**. The 4 warnings are deprecation notices from third-party libraries (starlette/httpx TestClient and shap colour maps), not failures.

### What each test checks

| Test | What it checks |
|---|---|
| `test_api.py::test_health` | `GET /health` returns `{"ok": true}`. |
| `test_api.py::test_action_approved_then_leaderboard` | A confident sapling (YOLO mocked at 0.9) is approved for 4 points and appears on both leaderboards (5 institutions, 10 users). |
| `test_api.py::test_duplicate_and_fraud_rejected` | Through the real API: the same photo twice → duplicate; Mumbai coordinates → geofence; client_time in 2020 → clock. All rejected. |
| `test_api.py::test_review_then_admin_approve` | A 0.45-confidence dumping report goes to needs_review. The admin queue needs the token (401 without it). Approval gives +2 and creates an open hotspot. |
| `test_api.py::test_cleanup_before_after_flow` | Littered before + clean after → approved (+5) and closes the hotspot ~55 m away. A still-littered after photo → rejected. |
| `test_api.py::test_cleanup_without_before_photo_is_400` | A cleanup without `before_photo` is refused with HTTP 400. |
| `test_dataset.py::test_fills_short_gaps_and_keeps_long_gaps` | Gap filling: a 3-hour gap is interpolated, a 4-hour gap stays empty. |
| `test_forecast.py::test_build_features_uses_no_future_data` | Leakage test: changing data after time t doesn't change any feature at t. |
| `test_forecast.py::test_target_is_pm25_24h_ahead` | The v1 target at row t equals PM2.5 at t+24, and the last 24 targets are empty. |
| `test_forecast.py::test_category_band_edges[...] (10 cases)` | CPCB band edges 30/31, 60/61, 90/91, 120/121, 250/251 map to the right category. |
| `test_forecast.py::test_mean24_target_is_mean_of_next_24_hours` | The v2 target at row t equals the mean PM2.5 of t+1 … t+24. |
| `test_forecast.py::test_future_weather_never_uses_future_pm25` | Leakage test for v2: with next-24 h weather features on, changing future PM2.5 doesn't change any feature at t. |
| `test_forecast.py::test_future_weather_is_next_24h_mean` | `fut_temp_mean24` at t equals the mean temperature of t+1 … t+24. |
| `test_scoring.py::test_points_by_type[...] (4 cases)` | Points when approved: sapling 4, segregated_bin 2, cleanup 5, dumping_report 2. |
| `test_scoring.py::test_week_starts_monday_midnight_ist` | The week starts Monday 00:00 IST; Sunday 23:59 IST belongs to the previous week. |
| `test_scoring.py::test_leaderboard_weekly_points` | Only this week's points count toward `points_week`; all points count toward the total; progress = points_week / 50. |
| `test_scoring.py::test_cleanup_within_150m_closes_hotspot` | A cleanup ~100 m away closes the hotspot; one ~500 m away doesn't. |
| `test_verify.py::test_clock_skew_rejected` | A photo 2 h old is rejected; 5 min is fine (limit 10 min). |
| `test_verify.py::test_outside_geofence_rejected` | Delhi centre (~30 km) is outside the 25 km geofence; the campus is inside. |
| `test_verify.py::test_same_image_twice_is_duplicate` | The second submission of the same image is caught by pHash. |
| `test_verify.py::test_resized_copy_is_duplicate_but_other_image_is_not` | A resized copy (400 → 360 px) is still a duplicate; a different picture is not. |
| `test_verify.py::test_decision_threshold_boundaries` | 0.60 → approved, 0.5999 → needs_review, 0.30 → needs_review, 0.2999 → rejected. |
| `test_verify.py::test_ai_check_rules_with_mocked_detections` | The COCO stand-in rules for each action type (sapling, bin, dumping top-2 mean, cleanup before/after counts). |

### Full `pytest -v` output (real, 2026-10-29)

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0 -- C:\dev\BIO-MANTRA-PROTOTYPE\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\dev\BIO-MANTRA-PROTOTYPE\backend
plugins: anyio-4.15.1
collecting ... collected 35 items

tests/test_api.py::test_health PASSED                                    [  2%]
tests/test_api.py::test_action_approved_then_leaderboard PASSED          [  5%]
tests/test_api.py::test_duplicate_and_fraud_rejected PASSED              [  8%]
tests/test_api.py::test_review_then_admin_approve PASSED                 [ 11%]
tests/test_api.py::test_cleanup_before_after_flow PASSED                 [ 14%]
tests/test_api.py::test_cleanup_without_before_photo_is_400 PASSED       [ 17%]
tests/test_dataset.py::test_fills_short_gaps_and_keeps_long_gaps PASSED  [ 20%]
tests/test_forecast.py::test_build_features_uses_no_future_data PASSED   [ 22%]
tests/test_forecast.py::test_target_is_pm25_24h_ahead PASSED             [ 25%]
tests/test_forecast.py::test_category_band_edges[30-Good] PASSED         [ 28%]
tests/test_forecast.py::test_category_band_edges[31-Satisfactory] PASSED [ 31%]
tests/test_forecast.py::test_category_band_edges[60-Satisfactory] PASSED [ 34%]
tests/test_forecast.py::test_category_band_edges[61-Moderately polluted] PASSED [ 37%]
tests/test_forecast.py::test_category_band_edges[90-Moderately polluted] PASSED [ 40%]
tests/test_forecast.py::test_category_band_edges[91-Poor] PASSED         [ 42%]
tests/test_forecast.py::test_category_band_edges[120-Poor] PASSED        [ 45%]
tests/test_forecast.py::test_category_band_edges[121-Very poor] PASSED   [ 48%]
tests/test_forecast.py::test_category_band_edges[250-Very poor] PASSED   [ 51%]
tests/test_forecast.py::test_category_band_edges[251-Severe] PASSED      [ 54%]
tests/test_forecast.py::test_mean24_target_is_mean_of_next_24_hours PASSED [ 57%]
tests/test_forecast.py::test_future_weather_never_uses_future_pm25 PASSED [ 60%]
tests/test_forecast.py::test_future_weather_is_next_24h_mean PASSED      [ 62%]
tests/test_scoring.py::test_points_by_type[sapling-4] PASSED             [ 65%]
tests/test_scoring.py::test_points_by_type[segregated_bin-2] PASSED      [ 68%]
tests/test_scoring.py::test_points_by_type[cleanup-5] PASSED             [ 71%]
tests/test_scoring.py::test_points_by_type[dumping_report-2] PASSED      [ 74%]
tests/test_scoring.py::test_week_starts_monday_midnight_ist PASSED       [ 77%]
tests/test_scoring.py::test_leaderboard_weekly_points PASSED             [ 80%]
tests/test_scoring.py::test_cleanup_within_150m_closes_hotspot PASSED    [ 82%]
tests/test_verify.py::test_clock_skew_rejected PASSED                    [ 85%]
tests/test_verify.py::test_outside_geofence_rejected PASSED              [ 88%]
tests/test_verify.py::test_same_image_twice_is_duplicate PASSED          [ 91%]
tests/test_verify.py::test_resized_copy_is_duplicate_but_other_image_is_not PASSED [ 94%]
tests/test_verify.py::test_decision_threshold_boundaries PASSED          [ 97%]
tests/test_verify.py::test_ai_check_rules_with_mocked_detections PASSED  [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\dev\BIO-MANTRA-PROTOTYPE\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

.venv\Lib\site-packages\shap\plots\colors\_colors.py:47
  C:\dev\BIO-MANTRA-PROTOTYPE\backend\.venv\Lib\site-packages\shap\plots\colors\_colors.py:47: PendingDeprecationWarning: The set_bad function will be deprecated in a future version. Use cmap.with_extremes(bad=...) or Colormap(bad=...) instead.
    red_blue.set_bad(gray_rgb.tolist(), 1.0)

.venv\Lib\site-packages\shap\plots\colors\_colors.py:48
  C:\dev\BIO-MANTRA-PROTOTYPE\backend\.venv\Lib\site-packages\shap\plots\colors\_colors.py:48: PendingDeprecationWarning: The set_over function will be deprecated in a future version. Use cmap.with_extremes(over=...) or Colormap(over=...) instead.
    red_blue.set_over(gray_rgb.tolist(), 1.0)

.venv\Lib\site-packages\shap\plots\colors\_colors.py:49
  C:\dev\BIO-MANTRA-PROTOTYPE\backend\.venv\Lib\site-packages\shap\plots\colors\_colors.py:49: PendingDeprecationWarning: The set_under function will be deprecated in a future version. Use cmap.with_extremes(under=...) or Colormap(under=...) instead.
    red_blue.set_under(gray_rgb.tolist(), 1.0)  # "under" is incorrectly used instead of "bad" in the scatter plot

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 35 passed, 4 warnings in 3.07s ========================
```

## 2. Manual fraud test (SPEC §12)

Copied from `raw/test_results.md`. Cases 1, 2 and 8 used **stand-in images**: COCO val2017 #139 as the plant and a generated wall texture. Cases 4 and 5 set the location and time in the request. Cases 3, 6 and 7 are **PENDING**: no result has been recorded or estimated for them.

| # | Case | Expected | Actual status | Confidence | Reasons |
|---|---|---|---|---|---|
| 1 | Potted plant photo (COCO stand-in) | approved or needs_review | needs_review | 0.421 | AI is not fully sure — sent to a coordinator |
| 2 | Same photo submitted again | rejected (duplicate) | rejected | – | this photo (or a near copy) was already submitted |
| 3 | Photo of a screen showing a plant image | record the honest result | **PENDING – needs real phone photo** | | |
| 4 | Far location (Mumbai coordinates) | rejected (geofence) | rejected | – | outside the allowed area; this photo (or a near copy) was already submitted |
| 5 | client_time 2 h old | rejected (clock) | rejected | – | photo time does not match server time; this photo (or a near copy) was already submitted |
| 6 | Cleanup, before littered → after clean | approved / needs_review | **PENDING – needs real phone photo** (before + after) | | |
| 7 | Cleanup, after still littered | rejected | **PENDING – needs real phone photo** (before + after) | | |
| 8 | Random photo (wall) as sapling | rejected | rejected | 0.0 | AI could not confirm the action |

## 3. Other checks that were run

- **Live API:** `start_demo.ps1 -Fresh` → `/health`, `/forecast?lang=en|hi`, `/meta`, `/leaderboard` and the website all returned HTTP 200 (`raw/api_check.txt`).
- **Action and admin endpoints with real YOLOv8n:** needs_review 0.421 → duplicate rejected → 400 without a before photo → 401 without a token → approve +4 → leaderboard updated (`raw/api_check_actions.txt`).
- **Demo flow run twice from a fresh database with 0 server errors:** `raw/demo_rehearsal.md`.
- **Model numbers:** `scripts/report_figures.py` recomputes the v2 test MAE (18.065) and checks it against `metrics.json` before drawing any figure.
- **UI:** headless Playwright screenshots of every page at 390×844 and 1366×768, with no horizontal overflow and no page errors reported.
- **APK:** `aapt dump badging` confirmed package `in.biomantra.app` with the CAMERA, FINE/COARSE LOCATION and INTERNET permissions. **Not yet tested on a phone.**
