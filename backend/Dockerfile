# Bio Mantra backend for a free Hugging Face Space (Docker SDK). Also runs anywhere Docker runs.
# Build context = backend/. Secrets/settings (ADMIN_TOKEN, LAT, LON, ...) come from Space variables, not files.
FROM python:3.11-slim

# System libraries: libgomp1 for LightGBM (OpenMP), libgl1 + libglib2.0-0 for OpenCV (pulled in by ultralytics)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# CPU-only PyTorch first (same versions as the laptop), so ultralytics doesn't pull the CUDA build
RUN pip install --no-cache-dir torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY models/lgbm.txt models/feature_list.json models/metrics.json ./models/
# Download the YOLOv8n weights at build time (official Ultralytics release), so start-up needs no download
RUN python -c "from ultralytics import YOLO; YOLO('models/yolov8n.pt')"

# Hugging Face runs the container as a non-root user; only /tmp is writable, and it is wiped on restart.
ENV BIOMANTRA_DB=/tmp/biomantra/biomantra.db \
    BIOMANTRA_UPLOADS=/tmp/biomantra/uploads \
    YOLO_CONFIG_DIR=/tmp/Ultralytics \
    MPLCONFIGDIR=/tmp/matplotlib \
    NUMBA_CACHE_DIR=/tmp/numba \
    WARM_MODELS=1 \
    PORT=7860
RUN mkdir -p /tmp/biomantra/uploads && chmod -R 777 /tmp/biomantra && chmod -R a+rX /app

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
