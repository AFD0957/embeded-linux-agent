#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO="${ROOT}/demo/icm20608-imx6ull"

echo "==> ELDA quickstart"
echo "    ELDA_ROOT=${ROOT}"

bash "${ROOT}/scripts/install_deps_ubuntu1604.sh"

export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
export PATH="/usr/local/bin:$PYENV_ROOT/bin:$PATH"
[[ -x "$PYENV_ROOT/bin/pyenv" ]] && eval "$("$PYENV_ROOT/bin/pyenv" init -)" 2>/dev/null || true

bash "${ROOT}/scripts/verify_install.sh"

if [[ ! -f "${ROOT}/secrets/api_keys.yaml" ]]; then
  cp "${ROOT}/secrets/api_keys.example.yaml" "${ROOT}/secrets/api_keys.yaml"
  echo "WARN: edit ${ROOT}/secrets/api_keys.yaml before running agents"
fi

bash "${ROOT}/scripts/compose.sh" up -d --build

echo "==> waiting for elda-api"
for _ in $(seq 1 60); do
  if curl -sf --max-time 2 http://127.0.0.1:8000/health >/dev/null; then
    echo "==> elda-api healthy"
    break
  fi
  sleep 3
done
curl -sf http://127.0.0.1:8000/health || {
  echo "ERROR: elda-api health check failed" >&2
  exit 1
}

bash "${DEMO}/scripts/bootstrap_demo.sh"

echo ""
echo "==> quickstart finished"
echo "    cd ${DEMO}"
echo "    terminal A: elda executor start"
echo "    terminal B: elda ingest && elda verify workspace && elda board add && elda plan && elda generate all && elda build && elda deploy"
