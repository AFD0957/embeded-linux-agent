#!/usr/bin/env bash
# Save Docker images for offline Ubuntu deploy
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/vendor/docker-images.tar"
mkdir -p "$ROOT/vendor"

echo "==> Pulling images..."
bash "$ROOT/scripts/compose.sh" pull

echo "==> Saving to $OUT (may take several minutes)..."
docker save \
  postgres:15-alpine \
  redis:7-alpine \
  minio/minio:latest \
  milvusdb/milvus:v2.3.4 \
  -o "$OUT"

echo "==> On Ubuntu offline: docker load -i vendor/docker-images.tar"
