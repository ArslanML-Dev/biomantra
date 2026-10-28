"""Bio Mantra FastAPI app: forecast, actions, leaderboard, hotspots and admin (SPEC §9)."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import get_conn, init_db
from app.forecast import get_forecast, load_model


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create and seed the database on startup."""
    init_db()
    yield


app = FastAPI(title="Bio Mantra API", lifespan=lifespan)
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


@app.get("/meta")
def meta() -> dict:
    """Users and institutions for the user picker, plus model metrics for the About page."""
    with get_conn() as conn:
        users = conn.execute("""SELECT u.id, u.name, u.institution_id, i.name AS institution
                                FROM users u JOIN institutions i ON i.id = u.institution_id
                                ORDER BY u.id""").fetchall()
        institutions = conn.execute("SELECT id, name FROM institutions ORDER BY id").fetchall()
    return {"users": [dict(r) for r in users], "institutions": [dict(r) for r in institutions],
            "model_metrics": load_model()[2]}
