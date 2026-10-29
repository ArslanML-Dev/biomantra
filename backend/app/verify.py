"""Anti-fraud gate and AI check for eco-action photos (SPEC §7). Cheap checks first, AI last."""
import ast
import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import imagehash
import numpy as np
import onnxruntime as ort
from PIL import Image

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_VERSION = "yolov8n-coco"
# YOLOv8n is the Ultralytics COCO model, exported once to ONNX (scripts/export_yolo_onnx.py) so the server
# needs only onnxruntime (~50 MB) instead of PyTorch (~1 GB). Settings = Ultralytics predict defaults.
YOLO_SIZE, YOLO_CONF, YOLO_IOU, YOLO_MAX_DET = 640, 0.25, 0.7, 300
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
def get_model() -> tuple[ort.InferenceSession, dict[int, str]]:
    """Load YOLOv8n (COCO, exported to ONNX) once, with its class names."""
    session = ort.InferenceSession(str(MODELS_DIR / "yolov8n.onnx"), providers=["CPUExecutionProvider"])
    names = ast.literal_eval(session.get_modelmeta().custom_metadata_map["names"])
    return session, names


def letterbox(image: Image.Image) -> tuple[np.ndarray, float, int, int]:
    """Resize keeping the aspect ratio and pad to 640x640 grey, like Ultralytics; return tensor, scale, padding."""
    w, h = image.size
    scale = min(YOLO_SIZE / w, YOLO_SIZE / h)
    nw, nh = round(w * scale), round(h * scale)
    left, top = round((YOLO_SIZE - nw) / 2 - 0.1), round((YOLO_SIZE - nh) / 2 - 0.1)
    canvas = Image.new("RGB", (YOLO_SIZE, YOLO_SIZE), (114, 114, 114))
    canvas.paste(image.resize((nw, nh), Image.BILINEAR), (left, top))
    tensor = np.asarray(canvas, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
    return tensor, scale, left, top


def nms(boxes: np.ndarray, scores: np.ndarray, iou_limit: float) -> list[int]:
    """Greedy non-maximum suppression: keep the best box, drop boxes overlapping it more than iou_limit."""
    order, keep = scores.argsort()[::-1], []
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    while order.size:
        best, rest = order[0], order[1:]
        keep.append(int(best))
        x1 = np.maximum(boxes[best, 0], boxes[rest, 0])
        y1 = np.maximum(boxes[best, 1], boxes[rest, 1])
        x2 = np.minimum(boxes[best, 2], boxes[rest, 2])
        y2 = np.minimum(boxes[best, 3], boxes[rest, 3])
        inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
        order = rest[inter / (areas[best] + areas[rest] - inter) <= iou_limit]
    return keep


def detect(image: Image.Image) -> list[dict]:
    """Run YOLOv8n on an image -> [{"name", "conf", "box": [x1, y1, x2, y2]}], best first."""
    session, names = get_model()
    tensor, scale, left, top = letterbox(image)
    preds = session.run(None, {"images": tensor})[0][0].T  # 8400 rows: cx, cy, w, h, 80 class scores
    cls = preds[:, 4:].argmax(1)
    conf = preds[:, 4:].max(1)
    preds, cls, conf = preds[conf >= YOLO_CONF], cls[conf >= YOLO_CONF], conf[conf >= YOLO_CONF]
    cx, cy, bw, bh = preds[:, 0], preds[:, 1], preds[:, 2], preds[:, 3]
    boxes = np.stack([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], axis=1)
    keep = nms(boxes + cls[:, None] * 7680.0, conf, YOLO_IOU)[:YOLO_MAX_DET]  # offset = per-class NMS
    w, h = image.size
    out = []
    for i in keep:
        x1, y1, x2, y2 = (boxes[i] - [left, top, left, top]) / scale
        box = [min(max(x1, 0), w), min(max(y1, 0), h), min(max(x2, 0), w), min(max(y2, 0), h)]
        out.append({"name": names[int(cls[i])], "conf": round(float(conf[i]), 3),
                    "box": [round(float(v), 1) for v in box]})
    return out


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
