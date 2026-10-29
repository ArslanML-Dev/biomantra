# Bio Mantra: user manual (install and run)

This is for running the prototype on a Windows laptop, with an Android phone on the same Wi-Fi. Commands are for **Windows PowerShell**, run in the project folder `C:\dev\BIO-MANTRA-PROTOTYPE` unless a step says otherwise.

## 0. What you need
- **Laptop:** Windows 10/11 with internet. The forecast fetches live data from Open-Meteo.
- **Software:** Python 3.11, Node.js 20 or newer, Git.
- **Phone:** an Android phone (Android 6.0 / API 23 or newer) on the **same Wi-Fi** as the laptop.
- **Network:** the Wi-Fi profile on the laptop set to **Private** (Settings → Network & internet → Wi-Fi → your network → Network profile type).

## 1. Backend: one-time setup
1. Open PowerShell and go to the backend:
   ```powershell
   cd C:\dev\BIO-MANTRA-PROTOTYPE\backend
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install CPU-only PyTorch first (this avoids a multi-GB GPU download), then the pinned requirements:
   ```powershell
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   ```
3. Create the settings file and edit it:
   ```powershell
   copy .env.example .env
   notepad .env
   ```
   - Set `LAT`/`LON` to your campus coordinates.
   - **Change `ADMIN_TOKEN`** to your own secret.
   - Never share or commit `.env`.
4. Check that everything works:
   ```powershell
   pytest -q
   ```
   It should say `35 passed`.

The trained model is already in `backend/models/`. The YOLOv8n weights (`yolov8n.pt`, about 6 MB) download automatically the first time a photo is checked.

## 2. Website: one-time setup
```powershell
cd C:\dev\BIO-MANTRA-PROTOTYPE\frontend
npm install
```

## 3. Start everything (every time)
1. In PowerShell:
   ```powershell
   cd C:\dev\BIO-MANTRA-PROTOTYPE
   powershell -ExecutionPolicy Bypass -File .\start_demo.ps1
   ```
   Add `-Fresh` for an empty database, for example before a demo.
2. Two server windows open. The script prints three addresses in big text:
   - **LAPTOP BROWSER:** `http://localhost:5173`
   - **PHONE BROWSER:** `http://<laptop-IP>:5173`
   - **PHONE APP, Settings → Server URL:** `http://<laptop-IP>:8000`
3. If a **Windows Security Alert** appears for `python.exe` or `node.exe`:
   - tick **Private networks**;
   - untick **Public networks**;
   - click **Allow access**. Don't click Cancel, because that blocks the phone.

   **Stricter option:** open PowerShell **as Administrator** once and run `powershell -ExecutionPolicy Bypass -File .\start_demo.ps1 -Firewall`. This opens only TCP ports 8000 and 5173, on Private networks only.
4. To stop, press **Enter** in the start-script window.

**Manual alternative** (two windows):
- Window 1: `cd backend; .venv\Scripts\activate; uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Window 2: `cd frontend; npm run dev -- --host`

## 4. Use the website (laptop)
1. Open `http://localhost:5173`.
2. Pick your name under **Who are you?**
3. **Home** shows tomorrow's PM2.5 (24-hour average), the CPCB category, the reason and a tip. Tap **EN / हिं** to switch language.
4. **Leaderboard** has Institutions and Users tabs, with weekly goal bars.
5. **Map** shows the forecast circle and red markers for open dumping hotspots.
6. **About** shows the model results, data sources and limitations.
7. **Admin** (top right):
   - enter the `ADMIN_TOKEN` from `backend/.env`;
   - **Approve** or **Reject** actions that the AI wasn't sure about.

On the website, **Act** only explains the actions. Photos can only be submitted from the app.

## 5. Install the app on the phone (APK)
The ready-made file is `C:\dev\BIO-MANTRA-PROTOTYPE\BioMantra.apk`. Pick **one** way to install it:
- **Without a cable:**
  1. Send `BioMantra.apk` to the phone (WhatsApp/Drive/email to yourself, or USB file copy).
  2. Open it on the phone.
  3. Allow **Install unknown apps** for that app when Android asks, then tap **Install**.
- **With a USB cable:**
  1. On the phone, go to Settings → About phone → tap **Build number** 7 times.
  2. Go to Settings → Developer options → turn on **USB debugging**.
  3. Connect the cable and tap **Allow** on the phone.
  4. On the laptop, run:
     ```powershell
     & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r C:\dev\BIO-MANTRA-PROTOTYPE\BioMantra.apk
     ```

**To rebuild the APK after code changes** (no Android Studio window needed):
```powershell
cd C:\dev\BIO-MANTRA-PROTOTYPE\frontend
powershell -ExecutionPolicy Bypass -File .\setup_android_sdk.ps1   # only once: Android SDK + JDK 21
powershell -ExecutionPolicy Bypass -File .\build_apk.ps1
```

## 6. Point the app at the laptop (Server URL)
1. Make sure `start_demo.ps1` is running and the phone is on the **same Wi-Fi** (not mobile data).
2. Open **Bio Mantra** on the phone and tap **⚙** (top right).
3. In **Server URL**, type the **PHONE APP** address the script printed, e.g. `http://192.168.1.19:8000`.
4. Tap **Test connection**. You should see **✓ Connected**.
5. Tap **Save**. The address is stored on the phone. Change it whenever the laptop's IP changes; **Reset to default** forgets it.
6. Go back to **Home** and pick your name. The forecast should appear.

## 7. Submit an eco-action (phone)
1. Tap **Act** and choose one:
   - Planted a sapling
   - Segregated waste
   - Cleaned up a spot
   - Report dumping
2. Tap **Take photo & submit**. Allow camera and location the first time.
   - Only the live camera is offered, never the gallery.
   - For **Cleaned up a spot**: take the **before** photo first, clean up, then take the **after** photo.
3. The result screen shows:
   - **approved** (points added straight away);
   - **needs review** (an admin decides);
   - **rejected** (with the reasons: wrong time, outside the area, duplicate photo, or AI could not confirm).
4. Points appear on the **Leaderboard** once an action is approved.

## 8. Troubleshooting
| Problem | Fix |
|---|---|
| **Test connection** fails | Same Wi-Fi? Address exactly as printed, including `http://` and `:8000`? Firewall allowed (step 3.3)? Wi-Fi profile Private? |
| "running scripts is disabled" | Start scripts with `powershell -ExecutionPolicy Bypass -File …` as shown |
| Forecast says "unavailable" | The laptop needs internet (Open-Meteo) |
| Photo always **rejected: time** | Set the phone's date and time to automatic |
| Photo **rejected: outside the allowed area** | The phone must be within 25 km of the campus coordinates in `.env` |
| Admin says invalid token | Use the exact `ADMIN_TOKEN` from `backend/.env` |
| `pip install` fails with "blocked by Application Control" | Keep the pinned versions in `requirements.txt`; Smart App Control blocks some newer packages |

*Health tips are general awareness, not medical advice.*
