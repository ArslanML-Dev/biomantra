"""Anti-fraud gate and AI check for eco-action photos (SPEC §7). Cheap checks first, AI last."""
import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import imagehash
from PIL import Image

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_VERSION = "yolov8n-coco"
LITTER = {"bottle", "cup", "bowl", "wine glass", "fork", "knife", "spoon"}
MIN_LITTER_CONF = 0.25

REASON_CLOCK = "photo time does not match server time"
REASON_GEOFENCE = "outside the allowed area"
REASON_DUPLICATE = "this photo (or a near copy) was already submitted"
REASON_APPROVED = "AI confirmed the action"
REASON_REVIEW = "AI is not fully sure — sent to a coordinator"
REASON_REJECTED = "AI could not confirm the action"


def check_clock(client_time: datetime, server_now: datetime, max_skew_min: float) -> str | None:
    """Reject if the phone's photo time is more than max_skew_min away from server time."""
    skew_min = abs((server_now - client_time).total_seconds()) / 60
    return REASON_CLOCK if skew_min > max_skew_min else None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def check_geofence(lat: float, lon: float, centre_lat: float, centre_lon: float,
                   radius_km: float) -> str | None:
    """Reject if the photo location is outside the allowed radius around the campus."""
    return REASON_GEOFENCE if haversine_km(lat, lon, centre_lat, centre_lon) > radius_km else None


def compute_phash(image: Image.Image) -> str:
    """Perceptual hash of an image as a hex string."""
    return str(imagehash.phash(image))


def check_duplicate(phash: str, existing: list[str], max_distance: int) -> str | None:
    """Reject if any stored hash is within max_distance bits (Hamming distance)."""
    new = imagehash.hex_to_hash(phash)
    for old in existing:
        if new - imagehash.hex_to_hash(old) <= max_distance:
            return REASON_DUPLICATE
    return None


@lru_cache(maxsize=1)
def get_model():
    """Load YOLOv8n (COCO) once and reuse it."""
    from ultralytics import YOLO
    MODELS_DIR.mkdir(exist_ok=True)
    return YOLO(str(MODELS_DIR / "yolov8n.pt"))


def detect(image: Image.Image) -> list[dict]:
    """Run YOLO on an image -> [{"name", "conf", "box": [x1, y1, x2, y2]}]."""
    result = get_model()(image, verbose=False)[0]
    return [{"name": result.names[int(cls)], "conf": round(float(conf), 3),
             "box": [round(float(v), 1) for v in box]}
            for cls, conf, box in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy)]


def litter_confs(detections: list[dict]) -> list[float]:
    """Confidences of litter objects (conf >= 0.25), highest first."""
    return sorted((d["conf"] for d in detections
                   if d["name"] in LITTER and d["conf"] >= MIN_LITTER_CONF), reverse=True)


def ai_check(action_type: str, detections: list[dict],
             before_detections: list[dict] | None = None) -> float:
    """Confidence (0–1) that the photo shows the claimed action, using COCO stand-in classes."""
    if action_type == "sapling":
        return max((d["conf"] for d in detections if d["name"] == "potted plant"), default=0.0)
    litter = litter_confs(detections)
    if action_type == "segregated_bin":
        return litter[0] if litter else 0.0
    if action_type == "dumping_report":
        return sum(litter[:2]) / 2 if len(litter) >= 2 else 0.0
    if action_type == "cleanup":
        before = len(litter_confs(before_detections or []))
        after = len(litter)
        return min(1.0, (before - after) / max(1, before)) if after < before else 0.0
    raise ValueError(f"unknown action_type: {action_type}")


def decide(confidence: float, auto_approve: float, review_floor: float) -> tuple[str, str]:
    """Turn an AI confidence into (status, reason)."""
    if confidence >= auto_approve:
        return "approved", REASON_APPROVED
    if confidence >= review_floor:
        return "needs_review", REASON_REVIEW
    return "rejected", REASON_REJECTED
