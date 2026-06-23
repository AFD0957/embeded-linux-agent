#!/usr/bin/env bash
# Install docker-compose 1.29.x to /usr/local/bin (Ubuntu 16.04 apt ships 1.8 — too old for ELDA).
set -euo pipefail

ELDA_COMPOSE_VERSION="${ELDA_COMPOSE_VERSION:-1.29.2}"
ELDA_CURL_CONNECT_TIMEOUT="${ELDA_CURL_CONNECT_TIMEOUT:-15}"
ELDA_CURL_MAX_TIME="${ELDA_CURL_MAX_TIME:-120}"
DEST="/usr/local/bin/docker-compose"
OS="$(uname -s)"
ARCH="$(uname -m)"
ASSET="docker-compose-${OS}-${ARCH}"
TMP="$(mktemp)"

cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

need_upgrade() {
  if [[ -x "$DEST" ]]; then
    :
  elif ! command -v docker-compose &>/dev/null; then
    return 0
  fi
  local ver
  ver="$(/usr/local/bin/docker-compose version --short 2>/dev/null || docker-compose version --short 2>/dev/null || true)"
  if [[ -z "$ver" ]]; then
    ver="$(docker-compose --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  fi
  if [[ -z "$ver" ]]; then
    return 0
  fi
  local major minor
  major="${ver%%.*}"
  minor="$(echo "$ver" | cut -d. -f2)"
  if [[ "$major" -gt 1 ]] || { [[ "$major" -eq 1 ]] && [[ "$minor" -ge 27 ]]; }; then
    echo "==> docker-compose $ver OK (need >= 1.27)"
    return 1
  fi
  echo "==> docker-compose $ver is too old (need >= 1.27); upgrading to $ELDA_COMPOSE_VERSION"
  return 0
}

download_one() {
  local url="$1"
  echo "    try (${ELDA_CURL_MAX_TIME}s max): $url"
  if curl -fsSL \
    --connect-timeout "$ELDA_CURL_CONNECT_TIMEOUT" \
    --max-time "$ELDA_CURL_MAX_TIME" \
    "$url" -o "$TMP"; then
    local size
    size="$(wc -c <"$TMP" | tr -d ' ')"
    if [[ "$size" -lt 1000000 ]]; then
      echo "    skip: download too small (${size} bytes), likely not the binary"
      return 1
    fi
    echo "    ok: ${size} bytes"
    return 0
  fi
  echo "    fail: timeout or HTTP error"
  return 1
}

if ! need_upgrade; then
  exit 0
fi

GITHUB_RELEASE="https://github.com/docker/compose/releases/download/${ELDA_COMPOSE_VERSION}/${ASSET}"

if [[ -n "${ELDA_COMPOSE_URL:-}" ]]; then
  URLS=("$ELDA_COMPOSE_URL")
else
  # mirror URLs first; GitHub release URL last
  URLS=(
    "https://mirror.ghproxy.com/${GITHUB_RELEASE}"
    "https://ghfast.top/${GITHUB_RELEASE}"
    "https://gh.llkk.cc/${GITHUB_RELEASE}"
    "https://ghp.ci/${GITHUB_RELEASE}"
    "${GITHUB_RELEASE}"
  )
fi

echo "==> Installing docker-compose ${ELDA_COMPOSE_VERSION} -> ${DEST}"
echo "    (CN mirrors first; each URL times out after ${ELDA_CURL_MAX_TIME}s)"
downloaded=0
for url in "${URLS[@]}"; do
  if download_one "$url"; then
    downloaded=1
    break
  fi
done

if [[ "$downloaded" -ne 1 ]]; then
  echo ""
  echo "ERROR: all download URLs failed or timed out." >&2
  echo "Manual install (try mirrors in order):" >&2
  echo "  sudo curl -fsSL --connect-timeout 15 --max-time 300 \\" >&2
  echo "    \"https://mirror.ghproxy.com/${GITHUB_RELEASE}\" \\" >&2
  echo "    -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose" >&2
  echo "Or set a mirror URL:" >&2
  echo "  ELDA_COMPOSE_URL='https://your-mirror/.../${ASSET}' bash scripts/install_docker_compose.sh" >&2
  exit 1
fi

sudo install -m 0755 "$TMP" "$DEST"
echo "==> $(docker-compose --version)"
