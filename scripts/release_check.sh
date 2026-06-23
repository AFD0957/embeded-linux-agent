#!/usr/bin/env bash
# Pre-release checks: secrets scan, git hygiene, repo completeness.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0
WARN=0

fail() {
  echo "[FAIL] $*"
  FAIL=$((FAIL + 1))
}

warn() {
  echo "[WARN] $*"
  WARN=$((WARN + 1))
}

ok() {
  echo "[OK]   $*"
}

echo "==> ELDA release check"
echo "    ELDA_ROOT=${ROOT}"
echo ""

echo "--- tracked secrets / credentials ---"
if git rev-parse --git-dir &>/dev/null 2>&1; then
  if git ls-files --error-unmatch .env &>/dev/null 2>&1; then
    fail ".env is tracked by git (must be gitignored)"
  else
    ok ".env not tracked"
  fi
  if git ls-files --error-unmatch secrets/api_keys.yaml &>/dev/null 2>&1; then
    fail "secrets/api_keys.yaml is tracked by git"
  else
    ok "secrets/api_keys.yaml not tracked"
  fi
  TRACKED="$(git ls-files 2>/dev/null || true)"
else
  warn "not a git repository — skip git ls-files checks"
  TRACKED="$(find . -type f \
    ! -path './.git/*' \
    ! -path './.venv/*' \
    ! -path './venv/*' \
    ! -path './__pycache__/*' \
    2>/dev/null || true)"
fi

echo ""
echo "--- hardcoded credential patterns ---"
scan_pattern() {
  local label="$1"
  local pattern="$2"
  local hit=0
  while IFS= read -r f; do
    [[ -n "$f" && -f "$f" ]] || continue
    [[ "$f" == "scripts/release_check.sh" ]] && continue
    if grep -qE "$pattern" "$f" 2>/dev/null; then
      hit=1
      echo "       $f"
    fi
  done <<< "$TRACKED"
  if [[ "$hit" -eq 1 ]]; then
    fail "found $label in tracked files"
  else
    ok "no $label in tracked files"
  fi
}

scan_pattern "eldaminio" 'eldaminio'
scan_pattern "postgres elda:elda URL" 'postgresql(\+asyncpg)?://elda:elda@'
scan_pattern "sk- API key" 'sk-[a-zA-Z0-9]{24,}'

echo ""
echo "--- personal / machine paths ---"
scan_pattern "personal path/username" '/home/[a-z]+|zhchen|14150'

echo ""
echo "--- required project files ---"
for f in LICENSE NOTICE README.md quickStart.md DEPENDENCIES.txt docker-compose.yml \
  .env.example secrets/api_keys.example.yaml \
  demo/icm20608-imx6ull/elda.yaml \
  demo/icm20608-imx6ull/board/imx6ull-elda-demo.dts \
  demo/icm20608-imx6ull/board/kernel.config.fragment \
  docs/assets/elda-banner.png \
  scripts/init_compose_env.sh scripts/release_check.sh; do
  if [[ -f "$f" ]]; then
    ok "$f"
  else
    fail "missing $f"
  fi
done

echo ""
echo "--- compose credential wiring ---"
if grep -q 'init_compose_env.sh first' docker-compose.yml; then
  ok "docker-compose requires generated .env credentials"
else
  fail "docker-compose missing required env credential guards"
fi

if grep -q '127.0.0.1:5432:5432' docker-compose.yml; then
  ok "postgres bound to localhost"
else
  warn "postgres may not be localhost-only"
fi

if [[ -f .env ]]; then
  if grep -qE '^ELDA_POSTGRES_PASSWORD=[a-f0-9]{32,}$' .env && \
     grep -qE '^ELDA_MINIO_SECRET_KEY=[a-f0-9]{32,}$' .env; then
    ok "local .env uses generated hex secrets"
  else
    warn "local .env exists but passwords may not be auto-generated format"
  fi
else
  ok "no local .env (expected before first compose up)"
fi

echo ""
echo "--- python syntax ---"
if command -v python &>/dev/null; then
  if python -m compileall -q elda/elda elda-api/app 2>/dev/null; then
    ok "python compileall"
  else
    fail "python compileall errors"
  fi
else
  warn "python not in PATH — skip compileall"
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "==> release check passed${WARN:+ ($WARN warning(s))}"
  exit 0
fi
echo "==> release check failed: $FAIL error(s)${WARN:+ , $WARN warning(s)}"
exit 1
