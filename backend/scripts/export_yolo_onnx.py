"""Export the pretrained YOLOv8n (COCO) weights to models/yolov8n.onnx for the slim server.

Needs the full dev install (ultralytics + onnx). Usage (from backend/):
    python scripts/export_yolo_onnx.py
"""
from pathlib import Path

from ultralytics import YOLO

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def main() -> None:
    """Export at 640 px with a fixed input size (what app/verify.py expects)."""
    path = YOLO(str(MODELS_DIR / "yolov8n.pt")).export(format="onnx", imgsz=640, simplify=False, dynamic=False)
    print("exported", path)


if __name__ == "__main__":
    main()
