"""API tests with FastAPI TestClient; YOLO is mocked (SPEC §12)."""
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
