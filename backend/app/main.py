"""Bio Mantra FastAPI app: forecast, actions, leaderboard, hotspots and admin (SPEC §9)."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.forecast import get_forecast

app = FastAPI(title="Bio Mantra API")
# No cookies/credentials are used (admin sends a header token), so allowing any origin is safe here;
# this covers the website, capacitor://localhost and http://localhost.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict:
    """Liveness check."""
    return {"ok": True}


@app.get("/forecast")
def forecast(lat: float = settings.LAT, lon: float = settings.LON,
             lang: str = Query("en", pattern="^(en|hi)$")) -> dict:
    """Tomorrow's PM2.5 forecast with category, SHAP reason and tip."""
    try:
        return get_forecast(lat, lon, lang)
    except Exception as err:  # network or upstream API failure
        raise HTTPException(503, f"forecast unavailable: {err}") from err
