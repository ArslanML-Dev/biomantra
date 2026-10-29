# Limitations (honest)

## Data
- **Modelled data, not CPCB station data.** PM2.5 comes from the Open-Meteo Air Quality API, which serves CAMS model/reanalysis estimates for a grid cell, not measurements from a CPCB ground monitoring station near campus. Local sources (a road, construction, burning) can make the real air on campus differ from the grid value. The model learns to forecast the *modelled* value.
- **Short history.** Open-Meteo PM2.5 starts on 2022-08-04: about 4 winters, 37,080 hourly rows. Rare "Severe" days are few. Only 26 test hours were Severe, and the model **never forecast "Severe"** in the test set (`figures/model_06_confusion_matrix.png`).
- **One location.** The model is trained for the campus coordinates only. Other `lat/lon` values sent to `/forecast` use the same model, which wasn't validated there.
- **No OpenWeather data.** The planned OpenWeather source wasn't used (no API key).

## Forecast model
- **The weather features are optimistic.** v2 uses next-24 h weather. Training and testing used the **actual** weather as a stand-in for a forecast, while the live app uses the Open-Meteo weather forecast, which has errors. The live accuracy will be **worse than the test MAE of 18.07 µg/m³**, somewhere between the "past only" (19.75) and the "past + weather" (18.07) results. It hasn't been measured live yet.
- **Moderate accuracy.** Test category accuracy is 0.559 and macro-F1 0.478: roughly 4 in 10 hours are put in the wrong CPCB category. Most errors are one category off. High values are under-forecast (`figures/model_01_predicted_vs_actual.png`).
- **The target changed.** v2 forecasts the mean over the next 24 h from the current hour. That's close to, but not the same as, the calendar-day (midnight-to-midnight) average CPCB reports.
- **SHAP reasons are simplified.** The sentence names the two largest SHAP contributions mapped to plain phrases. It explains the model, not the real physical cause.

## Photo verification (anti-fraud and AI)
- **COCO stand-in classes.** YOLOv8n is pretrained on COCO, which has no "sapling", "dustbin" or "garbage" class:
  - "potted plant" stands in for a sapling;
  - bottles, cups, bowls and cutlery stand in for litter.
  
  A clear plant scored only 0.421 (needs_review). Most real actions will need a human reviewer, and some may be wrongly rejected or approved.
- **The fraud gate can be beaten.** The clock, geofence and pHash checks raise the bar but can't stop:
  - a photo of a screen (fraud case 3, still PENDING);
  - GPS spoofing that stays inside the 25 km geofence;
  - a phone clock set on purpose (only the 10-minute skew is checked);
  - a new photo of the same scene from a different angle.
- **Limited real testing.** Fraud cases 3, 6 and 7 haven't been run with real phone photos. The cleanup logic is only tested with mocked YOLO.

## App, security and scope
- **Prototype security.** There are no user accounts or passwords (a simple user picker). Admin uses one shared token. CORS allows every origin. Dev builds of the APK allow cleartext HTTP to the laptop.
- **Not tested on a phone.** `BioMantra.apk` is built, but camera, GPS and submission haven't been tested on a real device yet.
- **Laptop-hosted demo.** The backend runs on the laptop (SQLite, local `uploads/`) and needs the phone on the same Wi-Fi. There's no cloud deployment, backup or scaling.
- **Health text.** Tips are rule-based general awareness, **not medical advice**, and say so in English and Hindi.
- **Sapling follow-up.** The "+3 at 30 days, +3 at 90 days" sapling bonus is only shown as pending; no re-check is built.
