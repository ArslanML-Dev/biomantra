"""Deploy the backend to a free Hugging Face Space (Docker) and wait until /health answers.

Needs a one-time login first (the user types their own token):
    deploy\\.venv\\Scripts\\python.exe -m huggingface_hub.cli.hf auth login
Usage (from the project root):
    deploy\\.venv\\Scripts\\python.exe deploy\\deploy_hf.py
Settings come from backend/.env (non-secret values become Space variables). ADMIN_TOKEN becomes a Space
*secret*: a new random token is created once and kept in deploy/admin_token.txt (git-ignored).
"""
import secrets
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
TOKEN_FILE = ROOT / "deploy" / "admin_token.txt"
SPACE_NAME = "biomantra-api"
PUBLIC_VARS = ["LAT", "LON", "GEOFENCE_RADIUS_KM", "AUTO_APPROVE", "REVIEW_FLOOR",
               "MAX_CLOCK_SKEW_MIN", "PHASH_MAX_DISTANCE"]
UPLOAD = ["Dockerfile", ".dockerignore", "requirements.txt", "app/*.py",
          "models/lgbm.txt", "models/feature_list.json", "models/metrics.json"]
README = """---
title: Bio Mantra API
emoji: 🌱
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---
Bio Mantra backend (FastAPI + LightGBM + YOLOv8n). Student prototype; data resets when the Space restarts.
"""


def read_env() -> dict[str, str]:
    """Key=value pairs from backend/.env."""
    pairs = {}
    for line in (BACKEND / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            pairs[key.strip()] = value.split("#")[0].strip()
    return pairs


def admin_token() -> str:
    """Reuse the saved deploy admin token, or create a new random one."""
    if not TOKEN_FILE.exists():
        TOKEN_FILE.write_text(secrets.token_urlsafe(18), encoding="utf-8")
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def main() -> None:
    """Create/update the Space, set its settings, upload the backend and wait for it to run."""
    api = HfApi()
    user = api.whoami()["name"]
    repo_id = f"{user}/{SPACE_NAME}"
    # Public, because the website and phone app must reach it without a Hugging Face login.
    api.create_repo(repo_id, repo_type="space", space_sdk="docker", private=False, exist_ok=True)
    env = read_env()
    for key in PUBLIC_VARS:
        if env.get(key):
            api.add_space_variable(repo_id, key, env[key])
    api.add_space_secret(repo_id, "ADMIN_TOKEN", admin_token())

    staging = ROOT / "deploy" / "README_space.md"
    staging.write_text(README, encoding="utf-8")
    api.upload_file(path_or_fileobj=str(staging), path_in_repo="README.md", repo_id=repo_id, repo_type="space")
    api.upload_folder(folder_path=str(BACKEND), repo_id=repo_id, repo_type="space", allow_patterns=UPLOAD,
                      commit_message="Deploy Bio Mantra backend")
    url = f"https://{user.lower().replace('_', '-').replace('.', '-')}-{SPACE_NAME}.hf.space"
    print(f"Space: https://huggingface.co/spaces/{repo_id}\nAPI:   {url}\nBuilding (first build takes ~5-15 min)...")

    for _ in range(120):  # up to 30 minutes
        stage = api.get_space_runtime(repo_id).stage
        try:
            if requests.get(f"{url}/health", timeout=20).json() == {"ok": True}:
                print(f"RUNNING: {url}/health -> ok")
                return
        except (requests.RequestException, ValueError):
            pass
        print(f"  stage: {stage}")
        if stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"):
            raise SystemExit(f"Space failed ({stage}); see the logs at https://huggingface.co/spaces/{repo_id}")
        time.sleep(15)
    raise SystemExit("Timed out waiting for the Space; check its logs.")


if __name__ == "__main__":
    main()
