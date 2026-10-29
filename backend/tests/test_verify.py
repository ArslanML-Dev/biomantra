"""Tests for the anti-fraud gate and decision rules (SPEC §12). YOLO is never loaded here."""
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw

from app import verify

NOW = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)
CAMPUS = (28.4725, 77.4889)


def make_image(seed: int, size: int = 400) -> Image.Image:
    """Draw a simple picture of shapes; different seeds give different pictures."""
    img = Image.new("RGB", (size, size), (200, 220, 200))
    draw = ImageDraw.Draw(img)
    for i in range(6):
        x, y = (seed * 37 + i * 61) % size, (seed * 53 + i * 89) % size
        draw.ellipse([x, y, x + size // 3, y + size // 4], fill=((seed * 40 + i * 30) % 255, 80, 40))
    return img


def test_clock_skew_rejected() -> None:
    """A photo 2 h old is rejected; 5 min is fine."""
    assert verify.check_clock(NOW - timedelta(hours=2), NOW, 10) == verify.REASON_CLOCK
    assert verify.check_clock(NOW - timedelta(minutes=5), NOW, 10) is None


def test_outside_geofence_rejected() -> None:
    """Delhi centre (~30 km away) is outside 25 km; the campus itself is inside."""
    assert verify.check_geofence(28.6139, 77.2090, *CAMPUS, 25) == verify.REASON_GEOFENCE
    assert verify.check_geofence(*CAMPUS, *CAMPUS, 25) is None


def test_same_image_twice_is_duplicate() -> None:
    """The second submission of the same image is caught."""
    stored: list[str] = []
    first = verify.compute_phash(make_image(1))
    assert verify.check_duplicate(first, stored, 6) is None
    stored.append(first)
    assert verify.check_duplicate(verify.compute_phash(make_image(1)), stored, 6) == verify.REASON_DUPLICATE


def test_resized_copy_is_duplicate_but_other_image_is_not() -> None:
    """A slightly resized copy is still caught by pHash; a different picture is not."""
    stored = [verify.compute_phash(make_image(1))]
    resized = make_image(1).resize((360, 360))
    assert verify.check_duplicate(verify.compute_phash(resized), stored, 6) == verify.REASON_DUPLICATE
    assert verify.check_duplicate(verify.compute_phash(make_image(7)), stored, 6) is None


def test_decision_threshold_boundaries() -> None:
    """0.30 and 0.60 are inclusive lower bounds of review and approve."""
    assert verify.decide(0.60, 0.60, 0.30)[0] == "approved"
    assert verify.decide(0.5999, 0.60, 0.30)[0] == "needs_review"
    assert verify.decide(0.30, 0.60, 0.30)[0] == "needs_review"
    assert verify.decide(0.2999, 0.60, 0.30)[0] == "rejected"


def test_ai_check_rules_with_mocked_detections() -> None:
    """Each action type uses its COCO stand-in rule."""
    plant = [{"name": "potted plant", "conf": 0.7, "box": [0, 0, 1, 1]}]
    litter = [{"name": "bottle", "conf": 0.8, "box": [0, 0, 1, 1]},
              {"name": "cup", "conf": 0.4, "box": [0, 0, 1, 1]}]
    assert verify.ai_check("sapling", plant) == 0.7
    assert verify.ai_check("sapling", litter) == 0.0
    assert verify.ai_check("segregated_bin", litter) == 0.8
    assert abs(verify.ai_check("dumping_report", litter) - 0.6) < 1e-9
    assert verify.ai_check("dumping_report", litter[:1]) == 0.0
    assert verify.ai_check("cleanup", [], before_detections=litter) == 1.0
    assert verify.ai_check("cleanup", litter[:1], before_detections=litter) == 0.5
    assert verify.ai_check("cleanup", litter, before_detections=litter) == 0.0


def test_real_onnx_yolo_on_sample_photos() -> None:
    """The real YOLOv8n ONNX model finds the potted plant (COCO #139) and nothing on a plain wall."""
    from pathlib import Path
    data = Path(__file__).parent / "data"
    plant = verify.detect(Image.open(data / "coco_139_plant.jpg").convert("RGB"))
    plant_conf = verify.ai_check("sapling", plant)
    assert 0.30 <= plant_conf < 0.60  # needs_review, as with the original PyTorch model (0.421)
    assert all(0 <= v for d in plant for v in d["box"])
    assert verify.detect(Image.open(data / "synthetic_wall.jpg").convert("RGB")) == []
