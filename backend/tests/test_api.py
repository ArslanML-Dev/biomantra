"""API tests with FastAPI TestClient; YOLO is mocked (SPEC §12)."""
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main, verify
from app.config import settings
from tests.test_verify import make_image

PLANT = [{"name": "potted plant", "conf": 0.9, "box": [10, 20, 200, 300]}]


@pytest.fixture
def client(fresh_db: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with a temp DB, temp uploads folder and a fake YOLO."""
    monkeypatch.setattr(main, "UPLOADS_DIR", fresh_db)
    monkeypatch.setattr(verify, "detect", lambda image: PLANT)
    with TestClient(main.app) as test_client:
        yield test_client


def jpeg_bytes(seed: int) -> bytes:
    """A test picture encoded as JPEG."""
    buf = io.BytesIO()
    make_image(seed).save(buf, "JPEG")
    return buf.getvalue()


def post_action(client: TestClient, seed: int = 1, **overrides) -> dict:
    """POST /actions with sensible defaults; overrides replace form fields."""
    data = {"user_id": 1, "action_type": "sapling", "lat": settings.LAT, "lon": settings.LON,
            "client_time": datetime.now(timezone.utc).isoformat()}
    data.update(overrides)
    resp = client.post("/actions", data=data, files={"photo": ("p.jpg", jpeg_bytes(seed), "image/jpeg")})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_health(client: TestClient) -> None:
    """GET /health is ok."""
    assert client.get("/health").json() == {"ok": True}


def test_action_approved_then_leaderboard(client: TestClient) -> None:
    """A confident sapling is approved for 4 points and shows on the leaderboard."""
    result = post_action(client)
    assert result["status"] == "approved" and result["points"] == 4
    assert result["detections"] == PLANT
    board = client.get("/leaderboard", params={"scope": "institutions"}).json()
    assert board[0]["name"] == "CSE-DS" and board[0]["points_week"] == 4
    users = client.get("/leaderboard", params={"scope": "users"}).json()
    assert users[0]["id"] == 1 and len(users) == 10


def test_duplicate_and_fraud_rejected(client: TestClient) -> None:
    """Same photo twice, far location and old client_time are rejected before AI."""
    post_action(client)
    assert verify.REASON_DUPLICATE in post_action(client)["reasons"]
    far = post_action(client, seed=5, lat=19.07, lon=72.87)
    assert far["status"] == "rejected" and verify.REASON_GEOFENCE in far["reasons"]
    old = post_action(client, seed=9, client_time="2020-01-01T00:00:00Z")
    assert old["status"] == "rejected" and verify.REASON_CLOCK in old["reasons"]


def test_review_then_admin_approve(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A 0.45 dumping report goes to review; admin approval gives points and a hotspot."""
    litter = [{"name": "bottle", "conf": 0.5, "box": [0, 0, 1, 1]},
              {"name": "cup", "conf": 0.4, "box": [0, 0, 1, 1]}]
    monkeypatch.setattr(verify, "detect", lambda image: litter)
    result = post_action(client, action_type="dumping_report")
    assert result["status"] == "needs_review" and result["points"] == 0
    assert client.get("/admin/review").status_code == 401
    headers = {"X-Admin-Token": settings.ADMIN_TOKEN}
    queue = client.get("/admin/review", headers=headers).json()
    assert [q["id"] for q in queue] == [result["id"]]
    done = client.post(f"/admin/review/{result['id']}", headers=headers,
                       json={"decision": "approve", "reviewer": "coordinator"}).json()
    assert done == {"id": result["id"], "status": "approved", "points": 2}
    assert client.get("/hotspots").json()[0]["open"] is True


def test_cleanup_before_after_flow(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Littered before + clean after is approved and closes a nearby hotspot; still littered is rejected."""
    bottle = {"name": "bottle", "conf": 0.8, "box": [0, 0, 1, 1]}
    monkeypatch.setattr(verify, "detect", lambda image: [bottle, bottle])
    report = post_action(client, action_type="dumping_report")
    assert report["status"] == "approved"
    assert client.get("/hotspots").json()[0]["open"] is True

    # before photo has 3 bottles, after photo has none (detect sees the after photo first, then before)
    calls = iter([[], [bottle] * 3])
    monkeypatch.setattr(verify, "detect", lambda image: next(calls))
    files = {"photo": ("after.jpg", jpeg_bytes(21), "image/jpeg"),
             "before_photo": ("before.jpg", jpeg_bytes(22), "image/jpeg")}
    data = {"user_id": 3, "action_type": "cleanup", "lat": settings.LAT + 0.0005, "lon": settings.LON,
            "client_time": datetime.now(timezone.utc).isoformat()}
    clean = client.post("/actions", data=data, files=files).json()
    assert clean["status"] == "approved" and clean["points"] == 5
    assert client.get("/hotspots").json()[0]["open"] is False

    monkeypatch.setattr(verify, "detect", lambda image: [bottle] * 3)
    files = {"photo": ("after.jpg", jpeg_bytes(31), "image/jpeg"),
             "before_photo": ("before.jpg", jpeg_bytes(32), "image/jpeg")}
    dirty = client.post("/actions", data=data, files=files).json()
    assert dirty["status"] == "rejected" and verify.REASON_REJECTED in dirty["reasons"]


def test_cleanup_without_before_photo_is_400(client: TestClient) -> None:
    """A cleanup must include the before photo."""
    resp = client.post("/actions", data={"user_id": 1, "action_type": "cleanup", "lat": settings.LAT,
                                         "lon": settings.LON, "client_time": datetime.now(timezone.utc).isoformat()},
                       files={"photo": ("p.jpg", jpeg_bytes(41), "image/jpeg")})
    assert resp.status_code == 400


def test_phone_photo_exif_rotation_is_applied(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A sideways-stored phone JPEG with EXIF orientation 6 reaches YOLO upright (portrait)."""
    seen = {}
    monkeypatch.setattr(verify, "detect", lambda image: seen.setdefault("size", image.size) and PLANT)
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation: rotate 90° clockwise to display
    buf = io.BytesIO()
    make_image(3).resize((400, 200)).save(buf, "JPEG", exif=exif)
    data = {"user_id": 1, "action_type": "sapling", "lat": settings.LAT, "lon": settings.LON,
            "client_time": datetime.now(timezone.utc).isoformat()}
    resp = client.post("/actions", data=data, files={"photo": ("p.jpg", buf.getvalue(), "image/jpeg")})
    assert resp.status_code == 200, resp.text
    assert seen["size"] == (200, 400)


def test_too_large_upload_is_413(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Uploads above the size limit are refused before decoding."""
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 1000)
    data = {"user_id": 1, "action_type": "sapling", "lat": settings.LAT, "lon": settings.LON,
            "client_time": datetime.now(timezone.utc).isoformat()}
    resp = client.post("/actions", data=data, files={"photo": ("p.jpg", jpeg_bytes(4), "image/jpeg")})
    assert resp.status_code == 413


def device_weather(hours_back: int = 72, hours_ahead: int = 48) -> dict:
    """An Open-Meteo-style hourly weather block around the current hour."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    times = [now + timedelta(hours=h) for h in range(-hours_back, hours_ahead)]
    n = len(times)
    return {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in times], "temperature_2m": [20.0] * n,
            "relative_humidity_2m": [60.0] * n, "wind_speed_10m": [5.0] * n,
            "wind_direction_10m": [180.0] * n, "precipitation": [0.0] * n}


def test_forecast_with_device_weather(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /forecast uses the device's weather (server weather fetch never called) and is not cached."""
    from app import forecast
    weather = device_weather()
    idx = pd.to_datetime(weather["time"], utc=True)
    monkeypatch.setattr(forecast, "fetch_air", lambda lat, lon: pd.DataFrame({"pm25": 80.0}, index=idx))
    monkeypatch.setattr(forecast, "fetch_hourly", lambda *a, **k: pytest.fail("server must not fetch weather"))
    forecast._cache.clear()
    resp = client.post("/forecast", json={"lang": "hi", "weather": weather})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["pm25_now"] == 80.0 and body["category"] and "चिकित्सा" in body["disclaimer"]
    assert forecast._cache == {}
    meta = client.get("/meta").json()
    assert meta["location"] == {"lat": settings.LAT, "lon": settings.LON}


def test_forecast_rejects_bad_device_weather(client: TestClient) -> None:
    """Out-of-range values, wrong lengths and gaps in time are refused with 422."""
    bad_rh = device_weather()
    bad_rh["relative_humidity_2m"][5] = 150
    short = device_weather()
    short["precipitation"] = short["precipitation"][:-1]
    gap = device_weather()
    del gap["time"][10]
    for weather in (bad_rh, short, gap):
        assert client.post("/forecast", json={"weather": weather}).status_code == 422
