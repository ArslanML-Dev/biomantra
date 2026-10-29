# Implementation story: real problems and how they were fixed

Every item below is taken from `docs/progress.md`, the git log (`raw/state.txt`), or command output saved in this pack. Where the records don't say *why* something happened, this file says so instead of guessing.

## 1. No OpenWeather key → Open-Meteo, and history only from Aug 2022
- **Plan:** PM2.5 history from the OpenWeather Air Pollution API from 2021-01-01.
- **Problem:** no OpenWeather key was available. Open-Meteo's air-quality history starts on **2022-08-04**, so the 2021 requests returned no rows.
- **Fix:** `fetch_history.py --source openmeteo` (the fallback allowed by the SPEC). 37,099 hourly rows, 2022-08-04 → 2026-10-27, 0 missing hours. Later, the live `/forecast` was also switched to Open-Meteo, so the model sees the same source in training and in use.
- **Commit:** `54aa409 feat: PM2.5 history download (Open-Meteo fallback)`.

## 2. Windows Smart App Control blocked new Python wheels
- **Problem:** Smart App Control (enforce mode) blocked the compiled `.pyd` files of the newest pandas 3.1.0, pyarrow 26.0.0, numba 0.68.1 and scikit-learn 1.9.1 ("An Application Control policy has blocked this file"). The imports failed with DLL-load errors.
- **Choice:** the team kept Smart App Control **on**. On many Windows builds, turning it off can't be undone without resetting Windows.
- **Fix:** pin older, widely used releases that already have reputation: **pandas 2.2.3, pyarrow 18.1.0, numpy 2.2.6, numba 0.61.2, llvmlite 0.44.0, scikit-learn 1.6.1** (`backend/requirements.txt`, commit `54aa409`). CPU-only PyTorch (2.14.1+cpu) is installed first, so Ultralytics doesn't pull the multi-GB CUDA build.

## 3. Move out of OneDrive
- **What happened:** the project was moved from the OneDrive Desktop folder to `C:\dev\BIO-MANTRA-PROTOTYPE`, and the virtual environment was rebuilt there (Python 3.11.9, CPU torch first, pinned requirements). The D1-T1 check was re-run (28.4725 77.4889), and all 3 commits so far were present (progress.md, 2026-10-28).
- **Why:** the progress log doesn't record the reason. *The team should add it here* (for example, sync/locking problems with the thousands of files in `.venv` and `node_modules`, if that's what happened).

## 4. Guarding against forecast leakage (no leakage bug was found)
- **What the records show:** there was **no leakage bug** in the committed code. Leakage was treated as a risk and tested from the start:
  - `test_build_features_uses_no_future_data` changes all data after time t and checks that the features at t don't change (commit `bc836e2`).
  - The time-ordered 70/15/15 split never shuffles.
- **v2 risk:** model v2 deliberately adds **next-24 h weather** features. To keep future **PM2.5** out of them, the test `test_future_weather_never_uses_future_pm25` was added.
- **v2 documentation:** the use of *actual* future weather as a stand-in for a forecast is documented as an optimistic assumption (`raw/model_experiments.md`).
- **Live inference:** PM2.5 values after the current hour (Open-Meteo also returns its own PM2.5 forecast) are explicitly blanked before the features are built (`fetch_live`).
- **A real bug caught before commit:** while writing the live `/forecast`, the first version read the "current PM2.5" from `pm25_lag_1`, which is the value one hour *earlier*. It was spotted in review and replaced with the actual PM2.5 at the prediction hour, before the code was committed (`01fc2ee`). This was a labelling bug in the response, not data leakage into the model.

## 5. Model v1 → v2: changing the target
- **v1** (D1-T5): target = PM2.5 exactly 24 h ahead, past features only. LightGBM test MAE **30.02**. It beat persistence (33.66) but only **tied** linear regression (29.97). Category accuracy was 0.399.
- **Why change:** CPCB AQI bands are defined on **24-hour averages**, so "tomorrow's category" should be predicted from the next-24 h mean, not a single hour. Tomorrow's weather is also a known driver (EDA: wind −0.17, temperature −0.38 correlation).
- **Experiment:** 2 targets × 2 feature sets × 3 models, all on the same 37,008 rows and split. The selection rule was fixed in advance: the 24-h-mean target, then the lowest **validation** MAE.
- **Result:** LightGBM with next-24 h weather. Test MAE **18.07** (linear 19.53, persistence 24.33), category accuracy **0.559**, recall for Poor-or-worse **0.771**. MAEs of different targets aren't directly comparable; that's explained in `raw/model_experiments.md`.
- **Commit:** `6fb9f7b`.

## 6. Android build without Android Studio, and Java 25 → 21
- **Problem 1:** Android Studio was installed but had never been opened, so there was no Android SDK.
- **Fix 1:** `frontend/setup_android_sdk.ps1` downloads Google's official command-line tools (13114758, SHA-1 checked) and sets `ANDROID_HOME`/`ANDROID_SDK_ROOT` for the user. It accepts the licences (on the user's instruction) and installs platform-tools, android-35 and build-tools 34.0.0. Every download is retried up to 3 times because the internet was slow.
- **Problem 2:** the first Gradle build failed with `Unsupported class file major version 69`. Android Studio's bundled JBR is **Java 25**, and the system Oracle JDK is 26. Gradle 8.11.1 (used by Capacitor 7 / AGP 8.7.2) can't run on either.
- **Fix 2:** a portable **Microsoft OpenJDK 21.0.13** (SHA-256 checked) in `%LOCALAPPDATA%\Android\jdk-21`, used only by `build_apk.ps1`. The next build said `BUILD SUCCESSFUL in 3m 31s` → `BioMantra.apk` (7.5 MB).
- **Problem 3:** the build retry loop didn't notice the failure, because the script didn't pass Gradle's exit code through.
- **Fix 3:** `build_apk.ps1` now stops with a clear error when any step fails.
- **Commit:** `b2bd4b9`.

## 7. The phone needs the laptop's changing Wi-Fi IP
- **Problem:** the APK had one backend address built in, and the laptop's Wi-Fi IP changes between networks.
- **Fix:** a ⚙ **Settings** page stores a "Server URL" on the device, with **Test connection** (`b0b0933`). `start_demo.ps1` starts the backend and the website and prints the exact addresses to type (`bc94c54`).
- **Firewall:** the script never changes the firewall itself. It explains which prompt to accept, and offers an optional Administrator mode that opens only TCP 8000/5173 on Private networks.

## 8. Smaller problems that cost time
- **Docs corrupted by PowerShell 5.1:** reading a UTF-8 file without a BOM through `Get-Content`/`Set-Content` turned "§" into "Â§" in `docs/TASKS.md` and added a BOM. It was fixed by restoring the file from git (`0923b85`), and docs were only edited with UTF-8-safe tools after that.
- **Fraud-test ordering:** rejected photos still store their pHash (on purpose). So the wall photo used for the geofence and clock cases had to be submitted as a sapling **first**; otherwise case 8 would have been reported as a "duplicate" instead of an AI rejection (`scripts/fraud_tests.py`).
- **Unticked tasks:** D2-T4 was ticked too early at first, then unticked, because its check (APK on a real phone) hadn't passed. Tasks whose check needs a phone or accounts stay unticked, with "WAITING FOR USER" in TASKS.md.
- **UI problems found by screenshots:** headless Playwright screenshots at phone size showed several problems, fixed in `853944b`:
  - a broken Admin header
  - a very long detection list
  - an English category name on the Hindi screen
  - a wrapped Hindi greeting
  - a cut-off About table
