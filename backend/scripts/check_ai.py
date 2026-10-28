"""Run the YOLO AI check on local images and print detections + decision (D1-T9 check).

Usage (from backend/):
    python scripts/check_ai.py sapling path/to/plant.jpg path/to/wall.jpg
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402
from app.verify import ai_check, decide, detect  # noqa: E402


def main() -> None:
    """Print detections, confidence and decision for each image as the given action type."""
    action_type, paths = sys.argv[1], sys.argv[2:]
    for path in paths:
        detections = detect(Image.open(path).convert("RGB"))
        conf = ai_check(action_type, detections)
        status, reason = decide(conf, settings.AUTO_APPROVE, settings.REVIEW_FLOOR)
        print(f"\n{path} as {action_type}:")
        for d in detections:
            print(f"  {d['name']:<14} conf={d['conf']:.3f} box={d['box']}")
        if not detections:
            print("  (no detections)")
        print(f"  -> confidence={conf:.3f} status={status} ({reason})")


if __name__ == "__main__":
    main()
