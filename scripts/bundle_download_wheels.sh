#!/usr/bin/env bash
# Download Python wheels into vendor/wheels for offline Ubuntu install
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WHEELS="$ROOT/vendor/wheels"
mkdir -p "$WHEELS"

PLATFORM="${ELDA_WHEEL_PLATFORM:-manylinux2014_x86_64}"
PYVER="${ELDA_WHEEL_PYVER:-3.11}"

echo "==> Downloading wheels to $WHEELS (platform=$PLATFORM python=$PYVER)"

pip download -d "$WHEELS" \
  --platform "$PLATFORM" --python-version "$PYVER" --only-binary=:all: \
  typer pydantic pyyaml httpx rich gitpython jinja2 pymilvus \
  fastapi "uvicorn[standard]" sqlalchemy asyncpg greenlet redis minio websockets pydantic-settings

# Editable installs need source — copy project itself
echo "==> Core wheels done. MinerU: see vendor/UBUNTU_ONLY.md"
echo "==> On Ubuntu offline:"
echo "    pip install --no-index --find-links=$WHEELS -e $ROOT/elda -e $ROOT/elda-api"
