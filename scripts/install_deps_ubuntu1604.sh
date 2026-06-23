#!/usr/bin/env bash
# ELDA dependencies for Ubuntu 16.04 LTS (China-friendly mirrors, resumable)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=lib/cn_mirrors.sh
source "$SCRIPT_DIR/lib/cn_mirrors.sh"

RESUME="${ELDA_SKIP_APT:-0}"

echo "==> ELDA install (Ubuntu 16.04, CN mirrors)"
echo "    ELDA_ROOT=$ROOT"
[[ "$RESUME" == "1" ]] && echo "    mode: RESUME (skip apt/docker/openssl if already done)"

if ! elda_is_xenial; then
  echo "Warning: this script targets Ubuntu 16.04; continuing anyway."
fi

# ── 1. apt + system packages ────────────────────────────────────────────────
if [[ "$RESUME" != "1" ]]; then
  bash "$SCRIPT_DIR/setup_apt_mirrors_cn.sh"

  echo "==> Installing system packages (apt)..."
  sudo apt-get install -y \
    build-essential curl git wget ca-certificates \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev \
    llvm \
    python3-pip \
    exuberant-ctags \
    device-tree-compiler \
    poppler-utils \
    docker.io docker-compose
else
  echo "==> Skipping apt (ELDA_SKIP_APT=1)"
fi

# ── 2. Docker ───────────────────────────────────────────────────────────────
if [[ "$RESUME" != "1" ]]; then
  setup_docker_cn() {
    sudo mkdir -p /etc/docker
    if [[ ! -f /etc/docker/daemon.json ]]; then
      local mirrors_json
      mirrors_json=$(printf '"%s",' "${ELDA_DOCKER_REGISTRY_MIRRORS[@]}")
      mirrors_json="[${mirrors_json%,}]"
      echo "{\"registry-mirrors\": ${mirrors_json}}" | sudo tee /etc/docker/daemon.json >/dev/null
      echo "==> Docker registry mirrors configured (DaoCloud / 163)"
    fi
    sudo service docker start || sudo systemctl start docker || true
    if ! groups "$USER" | grep -q '\bdocker\b'; then
      sudo usermod -aG docker "$USER"
      echo "==> Added $USER to docker group — log out and back in for permission without sudo"
    fi
  }
  setup_docker_cn
fi

# apt docker-compose on xenial is 1.8 — ELDA needs >= 1.27 (compose file v3 + healthcheck + depends_on conditions)
bash "$SCRIPT_DIR/install_docker_compose.sh"

# ── 3. ripgrep ──────────────────────────────────────────────────────────────
install_ripgrep_if_needed() {
  if command -v rg &>/dev/null; then
    echo "==> ripgrep: $(rg --version | head -1)"
    return 0
  fi
  echo "==> Installing ripgrep (static binary, CN mirror)"
  local tmp
  tmp="$(mktemp -d)"
  if ! elda_download_first "$tmp/$ELDA_RIPGREP_TARBALL" "${ELDA_RIPGREP_URLS[@]}"; then
    rm -rf "$tmp"
    echo "ERROR: could not download ripgrep" >&2
    exit 1
  fi
  tar -xzf "$tmp/$ELDA_RIPGREP_TARBALL" -C "$tmp"
  sudo install -m 0755 "$tmp/$ELDA_RIPGREP_NAME/rg" /usr/local/bin/rg
  rm -rf "$tmp"
  echo "==> ripgrep: $(rg --version | head -1)"
}
install_ripgrep_if_needed

# ── 4. OpenSSL 1.1 (xenial only) ────────────────────────────────────────────
OPENSSL_PREFIX="${HOME}/.local/openssl-${ELDA_OPENSSL_VERSION}"
install_openssl_if_needed() {
  if [[ -x "$OPENSSL_PREFIX/bin/openssl" ]]; then
    echo "==> OpenSSL already installed: $OPENSSL_PREFIX"
    return 0
  fi
  echo "==> Building OpenSSL ${ELDA_OPENSSL_VERSION} for pyenv (xenial ships 1.0.x)"
  local tmp src tarball
  tmp="$(mktemp -d)"
  tarball="$tmp/${ELDA_OPENSSL_TARBALL}"
  if ! elda_download_first "$tarball" "${ELDA_OPENSSL_TARBALL_URLS[@]}"; then
    rm -rf "$tmp"
    echo "ERROR: could not download OpenSSL ${ELDA_OPENSSL_VERSION} source tarball" >&2
    exit 1
  fi
  tar -xzf "$tarball" -C "$tmp"
  src="$tmp/openssl-${ELDA_OPENSSL_VERSION}"
  (
    cd "$src"
    ./config --prefix="$OPENSSL_PREFIX" --openssldir="$OPENSSL_PREFIX" shared zlib
    make -j"$(nproc)"
    make install_sw
  )
  elda_openssl_fix_symlinks "$OPENSSL_PREFIX"
  rm -rf "$tmp"
  echo "==> OpenSSL installed to $OPENSSL_PREFIX"
  elda_verify_openssl "$OPENSSL_PREFIX"
}
if elda_is_xenial; then
  install_openssl_if_needed
  elda_openssl_fix_symlinks "$OPENSSL_PREFIX"
  echo "==> OpenSSL check:"
  elda_verify_openssl "$OPENSSL_PREFIX" || exit 1
fi

# ── 5. pyenv + Python 3.11 ──────────────────────────────────────────────────
elda_ensure_pyenv
elda_ensure_pyenv_in_shell
eval "$(pyenv init -)" 2>/dev/null || true

export PYTHON_BUILD_MIRROR_URL="$ELDA_PYTHON_BUILD_MIRROR"
if elda_is_xenial; then
  elda_configure_pyenv_openssl "$OPENSSL_PREFIX"
fi

elda_pyenv_remove_broken_python "${ELDA_PYTHON_VERSION}"

if ! elda_pyenv_python_has_ssl "${ELDA_PYTHON_VERSION}"; then
  elda_prefetch_python_for_pyenv
  echo "==> Building Python ${ELDA_PYTHON_VERSION} via pyenv (compile 15–40 min, with OpenSSL)"
  pyenv install -f -v "${ELDA_PYTHON_VERSION}"
  if ! elda_pyenv_python_has_ssl "${ELDA_PYTHON_VERSION}"; then
    echo "ERROR: Python ${ELDA_PYTHON_VERSION} built but ssl module still missing" >&2
    exit 1
  fi
else
  echo "==> Python ${ELDA_PYTHON_VERSION} already installed (ssl OK)"
fi
pyenv global "${ELDA_PYTHON_VERSION}"
elda_ensure_pyenv_in_shell
# pip.conf (incl. prefer-binary on xenial) — before package install

echo "==> Python: $(python --version)"
if ! python -c "import ssl; print('ssl OK:', ssl.OPENSSL_VERSION)"; then
  echo "ERROR: python ssl check failed" >&2
  exit 1
fi

# ── 6. ELDA packages ────────────────────────────────────────────────────────
elda_pip_install_elda_packages "$ROOT"

chmod +x "$SCRIPT_DIR/compose.sh" "$SCRIPT_DIR/verify_install.sh" "$SCRIPT_DIR/setup_apt_mirrors_cn.sh" "$SCRIPT_DIR/install_docker_compose.sh" "$SCRIPT_DIR/quickstart.sh" "$SCRIPT_DIR/init_compose_env.sh" "$SCRIPT_DIR/release_check.sh"
chmod +x "$ROOT/demo/icm20608-imx6ull/scripts/"*.sh 2>/dev/null || true

echo ""
echo "==> Install finished."
echo ""
echo "IMPORTANT — open a NEW terminal (or run: source ~/.bashrc)"
echo "  python --version          # must show Python 3.11.x, NOT 2.7"
echo "  bash scripts/verify_install.sh"
echo ""
echo "Then:"
echo "  cp secrets/api_keys.example.yaml secrets/api_keys.yaml   # edit keys"
echo "  bash scripts/compose.sh up -d --build"
echo "  curl -s http://localhost:8000/health"
