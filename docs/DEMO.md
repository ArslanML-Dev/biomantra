# Bio Mantra: 2-minute demo

You need the laptop and the phone on the **same Wi-Fi**. Do the one-time setup the day before the demo.

---

## One-time setup (about 30 minutes, only once)

### A. App file: already built
`C:\dev\BIO-MANTRA-PROTOTYPE\BioMantra.apk` is ready. Its default server is `http://192.168.1.19:8000`, and you can change that in the app under ⚙ Settings.
To rebuild it after code changes, open PowerShell in `C:\dev\BIO-MANTRA-PROTOTYPE\frontend` and run `powershell -ExecutionPolicy Bypass -File .\build_apk.ps1`. The Android SDK and JDK 21 are already installed by `setup_android_sdk.ps1`, and Android Studio isn't needed.

### B. Put the app on the phone (pick one)
1. **Without a cable:** copy `BioMantra.apk` to the phone (WhatsApp/Drive/email it to yourself, or use a USB file transfer). Open it on the phone, and allow **"Install unknown apps"** when Android asks.
2. **With a USB cable:** on the phone, go to Settings → About phone → tap **Build number** 7 times → Settings → Developer options → turn on **USB debugging**. Connect the cable and tap **Allow** on the phone. Then, on the laptop, run:
   `& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r C:\dev\BIO-MANTRA-PROTOTYPE\BioMantra.apk`

### C. Firewall, so the phone can reach the laptop
3. Easiest: the first time you run the start script, a **Windows Security Alert** window may pop up for `python.exe` and `node.exe`. For each one:
   - tick **Private networks**
   - untick **Public networks**
   - click **Allow access**. Don't click Cancel, because that blocks the phone.
4. Tighter alternative (only ports 8000 and 5173 are opened, on private Wi-Fi only): right-click **Windows PowerShell → Run as administrator**, then run:
   `cd C:\dev\BIO-MANTRA-PROTOTYPE; powershell -ExecutionPolicy Bypass -File .\start_demo.ps1 -Firewall`

---

## The demo (2 minutes)

| Time | Do this | Say this |
|---|---|---|
| 0:00 | On the laptop, in `C:\dev\BIO-MANTRA-PROTOTYPE`, run `powershell -ExecutionPolicy Bypass -File .\start_demo.ps1 -Fresh`. Wait for the three green/blue boxes with the addresses. | "One script starts our FastAPI backend and React website." |
| 0:10 | In the laptop browser, open **http://localhost:5173** → pick a user → show the forecast card → tap **हिं**, then **EN**. | "LightGBM forecasts tomorrow's PM2.5. SHAP gives the one-line reason, in English or Hindi." |
| 0:30 | Click **Leaderboard** and leave it open on the projector. | "Points are per institution, with a weekly goal of 50." |
| 0:40 | On the phone, open **Bio Mantra** → ⚙ (top right) → **Server URL**: type the PHONE APP address from the laptop screen (e.g. `http://192.168.1.19:8000`) → **Test connection** (✓) → **Save**. | "The app talks to the laptop over Wi-Fi." |
| 0:55 | Phone: **Home** → pick a user → **Act** → **Planted a sapling** → **Take photo & submit** → photograph a plant → allow camera and location if asked. | "Live camera only, no gallery. The server checks time, location and duplicates, then YOLOv8 checks the photo." |
| 1:15 | Show the result screen: the status (usually **needs review**), the reasons, and what the AI saw. | "When the AI isn't sure, a human decides." |
| 1:25 | Laptop: open **http://localhost:5173/admin** → token `change-me` (or your `ADMIN_TOKEN`) → **Approve**. | "The coordinator approves it." |
| 1:40 | Laptop: click **Leaderboard** → the institution now has **+4** points. | "The approved action counts straight away." |
| 1:50 | Optional: phone → submit the **same photo again** → **rejected (duplicate)**. Then show **Map** and **About** (real metrics and limitations). | "Anti-fraud: the same picture can't score twice." |

When you're finished, press **Enter** in the start-script window to stop both servers.

### If something goes wrong
- **Test connection fails:** check the phone is on the same Wi-Fi (not mobile data). Check the address matches the "PHONE APP" line exactly. Then redo step 3 (the firewall).
- **Website on the phone browser:** open the "PHONE BROWSER" address. It finds the backend by itself.
- **Forecast says "unavailable":** the laptop needs internet, because the forecast fetches live air-quality data.
- **No needs-review item in admin:** the AI may have approved or rejected the photo outright. Take another photo with the plant clearly in view.
