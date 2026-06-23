#!/usr/bin/env bash
# Install ELDA from bundled wheels (offline-friendly)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WHEELS="$ROOT/vendor/wheels"

if [[ ! -d "$WHEELS" ]] || [[ -z "$(ls -A "$WHEELS" 2>/dev/null)" ]]; then
  echo "No vendor/wheels — run scripts/bundle_download_wheels.sh on online machine first"
  exit 1
fi

python3.11 -m venv "$ROOT/.venv"
source "$ROOT/.venv/bin/activate"
pip install --no-index --find-links="$WHEELS" -e "$ROOT/elda[dev,mineru]" -e "$ROOT/elda-api"
echo "==> Installed into $ROOT/.venv"
