#!/usr/bin/env bash
# Quick post-install checks for Ubuntu VM setup.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0
WARN=0

check() {
  local name="$1"
  shift
  if "$@" &>/dev/null; then
    echo "[OK]   $name"
  else
    echo "[FAIL] $name"
    FAIL=$((FAIL + 1))
  fi
}

echo "==> ELDA install verification"
echo "    ELDA_ROOT=$ROOT"
echo ""

export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
export PATH="$PYENV_ROOT/bin:$PATH"
if [[ -x "$PYENV_ROOT/bin/pyenv" ]]; then
  eval "$("$PYENV_ROOT/bin/pyenv" init -)" 2>/dev/null || true
elif [[ -d "$PYENV_ROOT" ]]; then
  echo "[WARN] ~/.pyenv exists but bin/pyenv missing — re-run install script"
  WARN=$((WARN + 1))
fi

if ! command -v pyenv &>/dev/null; then
  echo "[FAIL] pyenv not in PATH"
  echo "       Fix: ELDA_SKIP_APT=1 bash scripts/install_deps_ubuntu1604.sh"
  FAIL=$((FAIL + 1))
fi

check "python 3.11" bash -c '[[ "$(python --version 2>&1)" == Python\ 3.11* ]]'
check "elda CLI" command -v elda
check "git" command -v git
check "dtc" command -v dtc
check "rg (ripgrep)" command -v rg

# PDF ingest (16.04: pymupdf + pdftotext, not MinerU)
if python -c "import fitz" 2>/dev/null || command -v pdftotext &>/dev/null; then
  parts=()
  python -c "import fitz" 2>/dev/null && parts+=("pymupdf")
  command -v pdftotext &>/dev/null && parts+=("pdftotext")
  echo "[OK]   pdf_extract (${parts[*]:-backend})"
else
  echo "[FAIL] pdf_extract (pip install pymupdf && sudo apt install poppler-utils)"
  FAIL=$((FAIL + 1))
fi

check "docker" command -v docker
check "docker-compose >= 1.27" bash -c '
  export PATH="/usr/local/bin:$PATH"
  ver=""
  if command -v docker-compose &>/dev/null; then
    ver="$(docker-compose version --short 2>/dev/null || docker-compose --version 2>/dev/null | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -1)"
  fi
  [[ -n "$ver" ]] || exit 1
  major="${ver%%.*}"
  minor="$(echo "$ver" | cut -d. -f2)"
  [[ "$major" -gt 1 ]] || { [[ "$major" -eq 1 ]] && [[ "$minor" -ge 27 ]]; }
'

if command -v docker &>/dev/null; then
  if docker info &>/dev/null; then
    echo "[OK]   docker daemon"
  elif sudo docker info &>/dev/null; then
    echo "[WARN] docker daemon needs sudo — fix permissions (see below)"
    WARN=$((WARN + 1))
  else
    echo "[FAIL] docker daemon not running"
    echo "       Fix:"
    echo "         sudo service docker start"
    echo "         sudo docker info"
    FAIL=$((FAIL + 1))
  fi
fi

if [[ -f "$ROOT/secrets/api_keys.yaml" ]]; then
  echo "[OK]   secrets/api_keys.yaml exists"
else
  echo "[WARN] secrets/api_keys.yaml missing — copy from secrets/api_keys.example.yaml"
  WARN=$((WARN + 1))
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "==> All critical checks passed${WARN:+ ($WARN warning(s))}."
  if [[ $WARN -gt 0 ]] && command -v docker &>/dev/null && ! docker info &>/dev/null 2>&1; then
    echo ""
    echo "Docker group membership required — log out and back in after:"
    echo "  sudo usermod -aG docker \$USER"
    echo "  docker info"
  fi
  echo ""
  echo "Next:"
  echo "  cp secrets/api_keys.example.yaml secrets/api_keys.yaml"
  echo "  bash scripts/compose.sh up -d --build"
  echo "  curl -s http://localhost:8000/health"
  exit 0
fi

echo "==> $FAIL check(s) failed."
exit 1
