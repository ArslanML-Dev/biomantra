# Bio Mantra backend image (slim runtime: no PyTorch). Used by Render (render.yaml) and runs anywhere Docker runs.
# Build context = backend/. Settings and secrets (ADMIN_TOKEN, LAT, LON, ...) come from environment variables.
FROM python:3.11-slim

# libgomp1: OpenMP runtime needed by LightGBM on Linux
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY app ./app
COPY models/lgbm.txt models/feature_list.json models/metrics.json models/yolov8n.onnx ./models/

# Run as a normal user; the database and photos live in /tmp (wiped when the service restarts).
ENV BIOMANTRA_DB=/tmp/biomantra/biomantra.db \
    BIOMANTRA_UPLOADS=/tmp/biomantra/uploads \
    WARM_MODELS=1 \
    PORT=8000
RUN mkdir -p /tmp/biomantra/uploads && chmod -R 777 /tmp/biomantra && chmod -R a+rX /app \
    && useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
