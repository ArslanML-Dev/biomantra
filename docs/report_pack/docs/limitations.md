# Limitations (honest)

## Data
- **Modelled data, not CPCB station data.** PM2.5 comes from the Open-Meteo Air Quality API, which serves CAMS model/reanalysis estimates for a grid cell, not measurements from a CPCB ground monitoring station near campus. Local sources (a road, construction, burning) can make the real air on campus differ from the grid value. The model learns to forecast the *modelled* value.
- **Single location.** The model is trained and tested for the campus coordinates only. It **hasn't been checked for other cities**, even though `/forecast` accepts any `lat/lon`.
- **Short history.** Open-Meteo PM2.5 starts on 2022-08-04: about 4 winters, 37,080 hourly rows. "Severe" days are rare: only 26 test hours were Severe, and the model **never forecast "Severe"** in the test set (`figures/model_06_confusion_matrix.png`).
- **No OpenWeather data.** The planned OpenWeather source wasn't used (no API key).

## Forecast model
- **v2 scores are an upper bound.** v2 uses next-day (next-24 h) weather. Training and testing used the **actual** weather as a stand-in for a weather forecast. The live app uses the Open-Meteo forecast, which has errors, so real accuracy will be **worse than the test MAE of 18.07 µg/m³**, probably between the "past only" result (19.75) and 18.07. Live accuracy hasn't been measured yet.
- **Moderate accuracy.** Test category accuracy is 0.559 and macro-F1 0.478: about 4 in 10 hours land in the wrong CPCB category. Most errors are one category off. High values are under-forecast (`figures/model_01_predicted_vs_actual.png`).
- **Target vs CPCB day.** v2 forecasts the mean over the next 24 h from the current hour. That's close to, but not the same as, the calendar-day (midnight-to-midnight) average CPCB reports.
- **SHAP reasons are simplified.** The sentence names the two largest SHAP contributions mapped to plain phrases. It explains the model, not the real physical cause.

## Photo verification (anti-fraud and AI)
- **COCO stand-in classes, not a model trained on sapling/litter photos.** YOLOv8n is pretrained on COCO, which has no "sapling", "dustbin" or "garbage" class:
  - "potted plant" stands in for a sapling;
  - bottles, cups, bowls and cutlery stand in for litter.
  
  No model was trained or fine-tuned on real sapling, bin or litter photos. A clear plant scored only 0.421 (needs_review), so most real actions will need a human reviewer, and some may be wrongly rejected or approved.
- **The cleanup check doesn't compare places.** It only counts litter before vs after. In the real run (`raw/api_check_hotspots.txt`), an unrelated "after" photo (a bear, COCO #285) was approved at confidence 1.0 and closed the hotspot.
- **pHash can miss a reused photo** that has been heavily cropped, rotated, mirrored or edited, because only near-identical images (Hamming distance ≤ 6) are caught. A new photo of the same scene from another angle also passes.
- **GPS and the camera can be spoofed on a rooted phone.** Fake-GPS apps or a modified camera feed can defeat the geofence and the "live camera only" rule. The server only checks that the time is within 10 minutes and the position within 25 km.
- **A photo of a screen** may pass (fraud case 3, still PENDING with a real phone photo).
- **Limited real testing.** Fraud cases 3, 6 and 7 haven't been run with real phone photos. The cleanup and hotspot flow was run with real YOLO, but only on COCO stand-in photos.

## App, deployment and security
- **Local Wi-Fi deployment only.** The backend (FastAPI, SQLite, local `uploads/`) and the website run on the laptop, and the phone must be on the same Wi-Fi. Nothing is deployed to the cloud; there's no backup or scaling.
- **Simple user picker, no login.** Users pick a name; there are no accounts or passwords.
- **Admin token in `.env`.** The admin pages use one shared token (`ADMIN_TOKEN` in `backend/.env`, sent as a header). It's still the public default value from `.env.example` and must be changed before any demo.
- **Other prototype shortcuts.** CORS allows every origin, and dev builds of the APK allow cleartext HTTP to the laptop.
- **Not tested on a phone.** `BioMantra.apk` is built, but camera, GPS and submission haven't been tested on a real device.
- **Screenshots use a sample database.** The report screenshots show one real submission, plus 10 approved actions and 2 hotspots inserted directly for display. They're headless-browser captures of the website, not photos of the app on a phone.
- **Sapling follow-up.** The "+3 at 30 days, +3 at 90 days" sapling bonus is only shown as pending; no re-check is built.

## Health text
- **Awareness only, not medical advice.** Tips are rule-based by CPCB category, and every forecast says "This is general awareness, not medical advice." in English and Hindi.
