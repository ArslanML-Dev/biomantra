# Technology stack (exact versions, as installed on 2026-10-29)

Sources: `backend/requirements.txt`, `pip list` in `backend/.venv`, `frontend/package.json`, the `--version` output of each tool, `sdkmanager --list_installed`, and Windows system information.

## Backend (Python, `backend/requirements.txt`, all pinned with `==`)

| Package | Version | Used for |
|---|---|---|
| fastapi | 0.162.0 | REST API (`app/main.py`) |
| uvicorn[standard] | 0.54.0 | ASGI server |
| python-multipart | 0.0.32 | multipart photo uploads (`POST /actions`) |
| python-dotenv | 1.2.4 | reads `backend/.env` |
| requests | 2.34.2 | Open-Meteo API calls |
| pandas | 2.2.3 | data handling (older pin, see implementation_story.md) |
| pyarrow | 18.1.0 | `hourly.parquet` (older pin) |
| numpy | 2.2.6 | arrays (older pin) |
| scikit-learn | 1.6.1 | linear regression, scaler, metrics (older pin) |
| lightgbm | 4.7.0 | forecast model |
| shap | 0.51.0 | TreeExplainer reasons |
| numba / llvmlite | 0.61.2 / 0.44.0 | SHAP dependency (older pin) |
| matplotlib | 3.11.2 | plots and report figures |
| ultralytics | 8.4.191 | YOLOv8n (`yolov8n.pt`, COCO-pretrained) |
| ImageHash | 4.3.2 | perceptual hash (pHash) duplicate check |
| pillow | 12.3.0 | image reading and saving |
| pytest | 9.1.1 | tests |
| httpx | 0.28.1 | FastAPI TestClient |

These come in as dependencies (not pinned in requirements.txt, installed versions shown): torch 2.14.1+cpu and torchvision 0.29.1+cpu (installed first from the PyTorch CPU index), opencv-python 5.0.0.93, starlette 1.10.0, pydantic 2.14.1. Standard library: sqlite3 (database), math (haversine), secrets (token compare).

## Frontend (`frontend/package.json`, exact versions)

| Package | Version | Used for |
|---|---|---|
| react / react-dom | 19.1.10 | UI |
| react-router-dom | 7.18.4 | routes |
| leaflet / react-leaflet | 1.9.4 / 5.0.0 | map page |
| @capacitor/core, @capacitor/android | 7.6.9 | Android packaging |
| @capacitor/camera | 7.0.5 | live camera photo (no gallery) |
| @capacitor/geolocation | 7.1.8 | GPS position |
| @capacitor/cli (dev) | 7.6.9 | `cap add/sync` |
| vite (dev) | 7.3.7 | dev server and build |
| @vitejs/plugin-react (dev) | 5.2.0 | React in Vite |
| typescript (dev) | 5.9.3 | type checking |
| @types/react, @types/react-dom, @types/leaflet (dev) | 19.3.0, 19.3.0, 1.9.22 | types |
| playwright (dev) | 1.64.0 | headless screenshots for the report |

## Tools and runtimes

| Tool | Version |
|---|---|
| Python | 3.11.9 (`backend/.venv`) |
| Node.js / npm | v24.16.0 / 11.13.0 |
| Git | 2.54.0.windows.1 |
| Java for Android builds | Microsoft Build of OpenJDK 21.0.13 LTS (`%LOCALAPPDATA%\Android\jdk-21`) |
| Gradle (wrapper) | 8.11.1 |
| Android Gradle Plugin | 8.7.2 |
| Android SDK | platform-tools 37.0.1, platforms;android-35, build-tools;34.0.0 (compileSdk/targetSdk 35, minSdk 23) |
| Android SDK command-line tools | 13114758 (installed by `frontend/setup_android_sdk.ps1`) |
| Headless browser | Chrome Headless Shell 156.0.8078.4 (Playwright) |
| Machine-learning models | LightGBM v2 (`backend/models/lgbm.txt`), YOLOv8n COCO (`yolov8n.pt`, Ultralytics assets v8.4.0) |

## Hardware and OS used for development and the demo

| Item | Value |
|---|---|
| Laptop | ASUS Vivobook 16 (V3607VU) |
| CPU | Intel Core 5 210H, 8 cores / 12 threads (CPU-only; no GPU used) |
| RAM | 15.6 GB |
| OS | Windows 11 Home Single Language, version 10.0.26300 (build 26300), 64-bit, Smart App Control on |
| Phone | **Not known yet.** No phone has been connected to this PC; fill in the model after installing the APK |
