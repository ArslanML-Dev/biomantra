# POST /actions endpoint

Source: `backend/app/main.py` (48 lines in total), copied unchanged.

Lines 101–148:

```python
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
```
