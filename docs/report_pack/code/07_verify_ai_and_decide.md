# AI check (YOLOv8n, COCO stand-in classes) and the decision thresholds

Source: `backend/app/verify.py` (30 lines in total), copied unchanged.

Lines 73–102:

```python
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
```
