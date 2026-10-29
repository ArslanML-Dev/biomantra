"""Bio Mantra FastAPI app: forecast, actions, leaderboard, hotspots and admin (SPEC §9)."""
import io
import json
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Literal

from fastapi import FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel

from app import scoring, verify
from app.config import settings
from app.db import BACKEND_DIR, get_conn, init_db
from app.forecast import get_forecast, load_model

UPLOADS_DIR = Path(os.getenv("BIOMANTRA_UPLOADS", BACKEND_DIR / "uploads"))
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_TYPES = set(scoring.POINTS)
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # a 12 MP phone JPEG at quality 80 is about 3-5 MB


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create and seed the database on startup."""
    init_db()
    yield


app = FastAPI(title="Bio Mantra API", lifespan=lifespan)
# No cookies/credentials are used (admin sends a header token), so allowing any origin is safe here;
# this covers the website, capacitor://localhost and http://localhost.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


class ReviewDecision(BaseModel):
    """Body of POST /admin/review/{id}."""

    decision: Literal["approve", "reject"]
    reviewer: str


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


def parse_client_time(value: str) -> datetime:
    """Parse an ISO 8601 time from the phone; a time without zone is treated as UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise HTTPException(400, "client_time must be ISO 8601") from err
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


async def read_image(upload: UploadFile) -> Image.Image:
    """Read an uploaded file as an upright RGB image, or fail with 400 (not an image) / 413 (too big)."""
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"photo is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    try:
        image = Image.open(io.BytesIO(data))
    except UnidentifiedImageError as err:
        raise HTTPException(400, f"{upload.filename or 'file'} is not an image") from err
    # Phone cameras store sideways pixels plus an EXIF rotation tag; apply it so YOLO sees the photo upright.
    return ImageOps.exif_transpose(image).convert("RGB")


def save_image(image: Image.Image) -> str:
    """Save an image under uploads/ with a UUID name and return the file name."""
    name = f"{uuid.uuid4().hex}.jpg"
    image.save(UPLOADS_DIR / name, "JPEG", quality=90)
    return name


@app.post("/actions")
async def create_action(user_id: int = Form(...), action_type: str = Form(...),
                        lat: float = Form(...), lon: float = Form(...),
                        client_time: str = Form(...), photo: UploadFile = File(...),
                        before_photo: UploadFile | None = File(None)) -> dict:
    """Verify an eco-action photo (fraud gate, then YOLO) and store the result."""
    if action_type not in ACTION_TYPES:
        raise HTTPException(400, f"action_type must be one of {sorted(ACTION_TYPES)}")
    if action_type == "cleanup" and before_photo is None:
        raise HTTPException(400, "cleanup needs a before_photo")
    image = await read_image(photo)
    before_image = await read_image(before_photo) if action_type == "cleanup" else None
    server_now = datetime.now(timezone.utc)
    phash = verify.compute_phash(image)

    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone():
            raise HTTPException(404, "unknown user_id")
        stored = [r[0] for r in conn.execute("SELECT phash FROM actions").fetchall()]
        reasons = [r for r in (
            verify.check_clock(parse_client_time(client_time), server_now, settings.MAX_CLOCK_SKEW_MIN),
            verify.check_geofence(lat, lon, settings.LAT, settings.LON, settings.GEOFENCE_RADIUS_KM),
            verify.check_duplicate(phash, stored, settings.PHASH_MAX_DISTANCE),
        ) if r]

        detections: list[dict] = []
        confidence = None
        status = "rejected"
        if not reasons:  # AI runs only after the cheap checks pass
            detections = verify.detect(image)
            before = verify.detect(before_image) if before_image else None
            confidence = round(verify.ai_check(action_type, detections, before), 3)
            status, reason = verify.decide(confidence, settings.AUTO_APPROVE, settings.REVIEW_FLOOR)
            reasons.append(reason)

        action_id = conn.execute("""
            INSERT INTO actions (user_id, action_type, photo_path, before_photo_path, lat, lon,
              client_time, server_time, phash, status, reasons, confidence, detections, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            user_id, action_type, save_image(image),
            save_image(before_image) if before_image else None, lat, lon, client_time,
            server_now.isoformat(timespec="seconds"), phash, status, json.dumps(reasons),
            confidence, json.dumps(detections), verify.MODEL_VERSION)).lastrowid
        points = scoring.apply_approval(conn, action_id) if status == "approved" else 0
    if status == "approved" and action_type == "sapling":
        reasons.append(scoring.SAPLING_NOTE)
    return {"id": action_id, "status": status, "confidence": confidence, "points": points,
            "reasons": reasons, "detections": detections}


@app.get("/leaderboard")
def get_leaderboard(scope: Literal["users", "institutions"] = "institutions") -> list[dict]:
    """Ranked users or institutions with weekly goal progress."""
    with get_conn() as conn:
        return scoring.leaderboard(conn, scope, datetime.now(timezone.utc))


@app.get("/hotspots")
def hotspots() -> list[dict]:
    """All dumping hotspots; open = not yet cleaned up."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM hotspots ORDER BY id").fetchall()
    return [{"id": r["id"], "lat": r["lat"], "lon": r["lon"], "created_at": r["created_at"],
             "open": r["cleaned_action_id"] is None, "cleaned_at": r["cleaned_at"]} for r in rows]


def require_admin(token: str | None) -> None:
    """Reject the request unless the X-Admin-Token header matches ADMIN_TOKEN."""
    if not token or not secrets.compare_digest(token, settings.ADMIN_TOKEN):
        raise HTTPException(401, "invalid admin token")


@app.get("/admin/review")
def review_queue(x_admin_token: str | None = Header(None)) -> list[dict]:
    """Actions waiting for a human reviewer, with photo URLs and detections."""
    require_admin(x_admin_token)
    with get_conn() as conn:
        rows = conn.execute("""SELECT a.*, u.name AS user_name FROM actions a
                               JOIN users u ON u.id = a.user_id
                               WHERE a.status = 'needs_review' ORDER BY a.id""").fetchall()
    return [{"id": r["id"], "user_id": r["user_id"], "user_name": r["user_name"],
             "action_type": r["action_type"], "confidence": r["confidence"],
             "server_time": r["server_time"], "lat": r["lat"], "lon": r["lon"],
             "photo_url": f"/uploads/{r['photo_path']}",
             "before_photo_url": f"/uploads/{r['before_photo_path']}" if r["before_photo_path"] else None,
             "detections": json.loads(r["detections"] or "[]"),
             "reasons": json.loads(r["reasons"])} for r in rows]


@app.post("/admin/review/{action_id}")
def review_action(action_id: int, body: ReviewDecision,
                  x_admin_token: str | None = Header(None)) -> dict:
    """Approve (points given now) or reject an action that needs review."""
    require_admin(x_admin_token)
    with get_conn() as conn:
        row = conn.execute("SELECT status FROM actions WHERE id = ?", (action_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "action not found")
        if row["status"] != "needs_review":
            raise HTTPException(409, f"action is already {row['status']}")
        status = "approved" if body.decision == "approve" else "rejected"
        conn.execute("UPDATE actions SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE id = ?",
                     (status, body.reviewer, scoring.now_iso(), action_id))
        points = scoring.apply_approval(conn, action_id) if status == "approved" else 0
    return {"id": action_id, "status": status, "points": points}
