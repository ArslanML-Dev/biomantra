# Anti-fraud checks: clock, geofence, duplicate (pHash)

Source: `backend/app/verify.py` (32 lines in total), copied unchanged.

Lines 23–54:

```python
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
```
