"""Load Bio Mantra settings from backend/.env with safe defaults."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """All config values used by the backend (SPEC §3)."""

    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    LAT: float = float(os.getenv("LAT", "28.4725"))
    LON: float = float(os.getenv("LON", "77.4889"))
    GEOFENCE_RADIUS_KM: float = float(os.getenv("GEOFENCE_RADIUS_KM", "25"))
    AUTO_APPROVE: float = float(os.getenv("AUTO_APPROVE", "0.60"))
    REVIEW_FLOOR: float = float(os.getenv("REVIEW_FLOOR", "0.30"))
    MAX_CLOCK_SKEW_MIN: float = float(os.getenv("MAX_CLOCK_SKEW_MIN", "10"))
    PHASH_MAX_DISTANCE: int = int(os.getenv("PHASH_MAX_DISTANCE", "6"))
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "change-me")


settings = Settings()
