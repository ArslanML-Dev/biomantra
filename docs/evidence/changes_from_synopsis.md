# Changes from the synopsis / plan

The original synopsis document isn't in this repository. This list compares what was built with the plan in `docs/SPEC.md` and `docs/TASKS.md`. Please add any synopsis-specific items by hand.

| Planned | Built | Why |
|---|---|---|
| PM2.5 history from the OpenWeather Air Pollution API, from 2021-01-01 | Open-Meteo Air Quality API (the SPEC's fallback), from 2022-08-04 | No OpenWeather key was available; Open-Meteo's PM2.5 history starts in Aug 2022 |
| Live `/forecast` uses OpenWeather history + current | Open-Meteo air-quality API (past 3 days) + Open-Meteo weather forecast API | Keeps the live input from the same source the model was trained on |
| Latest library versions | pandas 2.2.3, pyarrow 18.1, numpy 2.2.6, scikit-learn 1.6.1, numba 0.61.2 | Windows Smart App Control blocked the DLLs of the newest wheels |
| CORS for specific origins | `allow_origins=["*"]` | No cookies or credentials are used (admin uses a header token), and Vercel/ngrok URLs weren't known in advance |
| LightGBM clearly best | LightGBM beats persistence (MAE 30.0 vs 33.7) but ties linear regression (30.0) | Real result, reported honestly. Suggested next step: predict the next-24 h mean instead of the single hour t+24 |
| `hour`/`dow`/`month` features | Computed in India time (IST) | So the daily pattern matches local life (the EDA shows a 22:00 IST peak) |
| Rejected photos | Their perceptual hash is still stored | Stops someone retrying the same photo with a fixed time or location |
| Debug APK installed on a phone | Android project, permissions and build script ready; APK not yet built | Android SDK not installed on the build PC (see HANDOFF.md) |
| Fraud test with real campus photos | 5 of 8 cases run with stand-in images (COCO photo, synthetic wall) | Real photos need the phone; script `scripts/fraud_tests.py` is ready |
