#!/usr/bin/env bash
# Docker Compose wrapper: Ubuntu 16.04 apt ships docker-compose 1.8 — use /usr/local/bin if upgraded.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT/docker-compose.yml"

if [[ ! -f "$ROOT/.env" ]]; then
  bash "$ROOT/scripts/init_compose_env.sh"
fi
cd "$ROOT"

compose_too_old() {
  local ver="${1:-}"
  [[ -z "$ver" ]] && return 0
  local major minor
  major="${ver%%.*}"
  minor="$(echo "$ver" | cut -d. -f2)"
  [[ "$major" -lt 1 ]] && return 0
  [[ "$major" -eq 1 && "$minor" -lt 27 ]]
}

compose_version_short() {
  "$1" version --short 2>/dev/null || "$1" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

run_compose() {
  local bin="$1"
  shift
  local ver
  ver="$(compose_version_short "$bin")"
  if compose_too_old "$ver"; then
    echo "ERROR: docker-compose ${ver:-unknown} is too old (need >= 1.27)." >&2
    echo "Run: bash scripts/install_docker_compose.sh" >&2
    exit 1
  fi
  exec "$bin" -f "$COMPOSE_FILE" "$@"
}

export PATH="/usr/local/bin:$PATH"

if docker compose version &>/dev/null 2>&1; then
  exec docker compose -f "$COMPOSE_FILE" "$@"
fi

if [[ -x /usr/local/bin/docker-compose ]]; then
  run_compose /usr/local/bin/docker-compose "$@"
fi
if command -v docker-compose &>/dev/null; then
  run_compose "$(command -v docker-compose)" "$@"
fi

echo "ERROR: neither 'docker compose' nor 'docker-compose' found." >&2
echo "Run: bash scripts/install_docker_compose.sh" >&2
exit 1
