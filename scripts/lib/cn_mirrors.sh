#!/usr/bin/env bash
# Shared China-accessible mirror URLs and download helpers for ELDA install scripts.

# pip
ELDA_PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

# Python source tarball (pyenv install) — repo.huaweicloud.com, NOT mirrors.huaweicloud.com
ELDA_PYTHON_VERSION="3.11.9"
ELDA_PYTHON_TARBALL="Python-${ELDA_PYTHON_VERSION}.tar.xz"
ELDA_PYTHON_BUILD_MIRROR="https://repo.huaweicloud.com/python"
ELDA_PYTHON_TARBALL_URLS=(
  "${ELDA_PYTHON_BUILD_MIRROR}/${ELDA_PYTHON_VERSION}/${ELDA_PYTHON_TARBALL}"
  "https://npmmirror.com/mirrors/python/${ELDA_PYTHON_VERSION}/${ELDA_PYTHON_TARBALL}"
  "https://www.python.org/ftp/python/${ELDA_PYTHON_VERSION}/${ELDA_PYTHON_TARBALL}"
)

# OpenSSL 1.1 (Ubuntu 16.04 ships 1.0.x; Python 3.11 needs 1.1+)
ELDA_OPENSSL_VERSION="1.1.1w"
ELDA_OPENSSL_TARBALL="openssl-${ELDA_OPENSSL_VERSION}.tar.gz"
ELDA_OPENSSL_TARBALL_URLS=(
  "https://ghfast.top/https://github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/${ELDA_OPENSSL_TARBALL}"
  "https://mirror.ghproxy.com/https://github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/${ELDA_OPENSSL_TARBALL}"
  "https://github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/${ELDA_OPENSSL_TARBALL}"
  "http://ftp.openssl.org/source/${ELDA_OPENSSL_TARBALL}"
  "https://www.openssl.org/source/${ELDA_OPENSSL_TARBALL}"
)

# ripgrep static binary (not in xenial apt)
ELDA_RIPGREP_VERSION="14.1.0"
ELDA_RIPGREP_NAME="ripgrep-${ELDA_RIPGREP_VERSION}-x86_64-unknown-linux-musl"
ELDA_RIPGREP_TARBALL="${ELDA_RIPGREP_NAME}.tar.gz"
ELDA_RIPGREP_URLS=(
  "https://ghfast.top/https://github.com/BurntSushi/ripgrep/releases/download/${ELDA_RIPGREP_VERSION}/${ELDA_RIPGREP_TARBALL}"
  "https://mirror.ghproxy.com/https://github.com/BurntSushi/ripgrep/releases/download/${ELDA_RIPGREP_VERSION}/${ELDA_RIPGREP_TARBALL}"
  "https://github.com/BurntSushi/ripgrep/releases/download/${ELDA_RIPGREP_VERSION}/${ELDA_RIPGREP_TARBALL}"
)

# pyenv installer / git clone fallbacks
ELDA_PYENV_INSTALLER_URLS=(
  "https://ghfast.top/https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer"
  "https://mirror.ghproxy.com/https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer"
  "https://pyenv.run"
)

# Docker Hub pull mirror (daemon.json)
ELDA_DOCKER_REGISTRY_MIRRORS=(
  "https://docker.m.daocloud.io"
  "https://hub-mirror.c.163.com"
)

# apt mirrors — name|base_url (no trailing slash)
# Ubuntu 16.04 xenial: packages live on regular /ubuntu/ (NOT ubuntu-old-releases).
# old-releases is for 14.04 trusty and older. Use HTTP on xenial (no apt-transport-https needed).
ELDA_APT_XENIAL_MIRRORS=(
  "tuna|http://mirrors.tuna.tsinghua.edu.cn/ubuntu"
  "ustc|http://mirrors.ustc.edu.cn/ubuntu"
  "aliyun|http://mirrors.aliyun.com/ubuntu"
  "huawei|http://mirrors.huaweicloud.com/ubuntu"
  "163|http://mirrors.163.com/ubuntu"
  "archive|http://archive.ubuntu.com/ubuntu"
)

ELDA_APT_CURRENT_MIRRORS=(
  "tuna|https://mirrors.tuna.tsinghua.edu.cn/ubuntu"
  "ustc|https://mirrors.ustc.edu.cn/ubuntu"
  "huawei|https://mirrors.huaweicloud.com/ubuntu"
  "aliyun|http://mirrors.aliyun.com/ubuntu"
  "archive|http://archive.ubuntu.com/ubuntu"
)

elda_is_gzip_file() {
  local f="$1"
  [[ -s "$f" ]] || return 1
  local magic
  magic=$(head -c 2 "$f" | od -An -tx1 | tr -d ' \n')
  [[ "$magic" == "1f8b" ]] || return 1
  gzip -t "$f" 2>/dev/null
}

elda_is_valid_python_tarball() {
  local f="$1"
  local size
  [[ -s "$f" ]] || return 1
  size=$(wc -c <"$f" | tr -d ' ')
  # Python-3.11.9.tar.xz is ~19 MB; reject HTML error pages
  [[ "$size" -ge 15000000 ]] || return 1
  return 0
}

elda_download_with_progress() {
  local dest="$1"
  shift
  local url
  for url in "$@"; do
    echo "    try: $url"
    if curl -4 -fL --connect-timeout 30 --retry 2 --retry-delay 2 --progress-bar "$url" -o "$dest"; then
      if [[ "$(basename "$dest")" == Python-*.tar.xz ]] && ! elda_is_valid_python_tarball "$dest"; then
        echo "    WARN: file too small or invalid (not Python source tarball)"
        rm -f "$dest"
        continue
      fi
      echo "    saved: $dest ($(du -h "$dest" | cut -f1))"
      return 0
    fi
    echo "    WARN: download failed"
  done
  return 1
}

elda_download_first() {
  local dest="$1"
  shift
  local url
  local want_gzip=0
  if [[ "$dest" == *.gz || "$dest" == *.tgz ]]; then
    want_gzip=1
  fi
  for url in "$@"; do
    echo "    try: $url"
    if curl -4 -fsSL --connect-timeout 30 --retry 2 --retry-delay 2 "$url" -o "$dest"; then
      if [[ "$want_gzip" -eq 1 ]] && ! elda_is_gzip_file "$dest"; then
        echo "    WARN: response is not a valid .tar.gz (likely HTML error page)"
        rm -f "$dest"
        continue
      fi
      return 0
    fi
    echo "    WARN: download failed"
  done
  return 1
}

elda_codename() {
  lsb_release -cs 2>/dev/null || echo "xenial"
}

elda_is_xenial() {
  [[ "$(lsb_release -rs 2>/dev/null || true)" == "16.04" ]] \
    || [[ "$(elda_codename)" == "xenial" ]]
}

elda_apt_mirror_candidates() {
  if elda_is_xenial; then
    printf '%s\n' "${ELDA_APT_XENIAL_MIRRORS[@]}"
  else
    printf '%s\n' "${ELDA_APT_CURRENT_MIRRORS[@]}"
  fi
}

elda_apt_write_sources() {
  local base="$1"
  local codename="$2"
  local label="$3"
  sudo tee /etc/apt/sources.list.d/elda-cn.list >/dev/null <<EOF
# ELDA: ${label} mirror (IPv4). Ubuntu ${codename}.
deb ${base}/ ${codename} main restricted universe multiverse
deb ${base}/ ${codename}-updates main restricted universe multiverse
deb ${base}/ ${codename}-backports main restricted universe multiverse
deb ${base}/ ${codename}-security main restricted universe multiverse
EOF
}

elda_apt_prepare_system() {
  sudo mkdir -p /etc/apt/apt.conf.d
  echo 'Acquire::ForceIPv4 "true";' | sudo tee /etc/apt/apt.conf.d/99elda-force-ipv4 >/dev/null

  if [[ -f /etc/apt/sources.list ]] && [[ ! -f /etc/apt/sources.list.bak.elda ]]; then
    sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak.elda
    echo "==> Backed up /etc/apt/sources.list → sources.list.bak.elda"
  fi

  if [[ -f /etc/apt/sources.list ]]; then
    sudo sed -i 's/^[[:space:]]*deb /# &/' /etc/apt/sources.list || true
  fi

  sudo rm -f /etc/apt/sources.list.d/elda-tuna.list /etc/apt/sources.list.d/elda-cn.list
}

elda_apt_setup_cn() {
  local codename="$1"
  local name base

  elda_apt_prepare_system

  echo "==> Trying apt mirrors for ${codename}..."
  if elda_is_xenial; then
    echo "    Note: xenial (16.04) uses regular /ubuntu/ — NOT ubuntu-old-releases"
  fi

  while IFS='|' read -r name base; do
    [[ -n "$name" && -n "$base" ]] || continue
    echo ""
    echo "==> Mirror: ${name} (${base})"
    elda_apt_write_sources "$base" "$codename" "$name"
    if sudo apt-get update -o Acquire::Retries=2; then
      echo "==> apt mirror OK (${name})"
      return 0
    fi
    echo "    WARN: apt-get update failed, trying next mirror..."
  done < <(elda_apt_mirror_candidates)

  echo "ERROR: all apt mirrors failed for ${codename}" >&2
  echo "  Try manually: sudo nano /etc/apt/sources.list.d/elda-cn.list" >&2
  return 1
}

# Ubuntu 16.04 / GCC 5.4: must use wheels — source builds need GCC >= 9.3 or C++11
ELDA_XENIAL_WHEEL_PINS=(
  "numpy==1.26.4"
  "pandas==2.2.3"
  "greenlet==3.1.1"
)

elda_configure_pip_cn() {
  mkdir -p "$HOME/.pip"
  cat >"$HOME/.pip/pip.conf" <<EOF
[global]
index-url = ${ELDA_PIP_INDEX}
trusted-host = pypi.tuna.tsinghua.edu.cn
prefer-binary = true
EOF
  if elda_is_xenial; then
    cat >>"$HOME/.pip/pip.conf" <<EOF
# Ubuntu 16.04: never compile these (GCC 5.4 / old g++)
only-binary = numpy,pandas,greenlet,grpcio,uvloop,httptools,watchfiles,pydantic-core,lxml,cryptography,orjson
EOF
  fi
  echo "==> pip mirror: ${ELDA_PIP_INDEX} (prefer-binary)"
}

elda_pip_preinstall_xenial_wheels() {
  if ! elda_is_xenial; then
    return 0
  fi
  echo "==> Pre-installing wheels for Ubuntu 16.04 (GCC 5.4 cannot build numpy/pandas/greenlet)"
  pip install --only-binary=:all: "${ELDA_XENIAL_WHEEL_PINS[@]}"
}

elda_pyenv_shell_snippet() {
  cat <<'EOF'
# ELDA / pyenv (added by install_deps_ubuntu1604.sh)
export PYENV_ROOT="$HOME/.pyenv"
[[ -d "$PYENV_ROOT/bin" ]] && export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv &>/dev/null; then
  eval "$(pyenv init -)"
fi
EOF
}

elda_verify_openssl() {
  local prefix="$1"
  local lib="${prefix}/lib"
  if [[ ! -x "${prefix}/bin/openssl" ]]; then
    echo "ERROR: OpenSSL binary missing: ${prefix}/bin/openssl" >&2
    return 1
  fi
  if [[ ! -f "${lib}/libssl.so.1.1" ]]; then
    echo "ERROR: ${lib}/libssl.so.1.1 not found — OpenSSL build incomplete" >&2
    return 1
  fi
  # Custom prefix: must set LD_LIBRARY_PATH to run openssl CLI (normal on 16.04)
  LD_LIBRARY_PATH="${lib}:${LD_LIBRARY_PATH:-}" "${prefix}/bin/openssl" version
}

elda_configure_pyenv_openssl() {
  local prefix="$1"
  if [[ ! -x "$prefix/bin/openssl" ]]; then
    echo "ERROR: OpenSSL not found at $prefix" >&2
    return 1
  fi
  elda_openssl_fix_symlinks "$prefix"
  echo "==> OpenSSL for Python build:"
  elda_verify_openssl "$prefix"
  # --with-openssl-rpath=auto: embed rpath so _ssl finds libssl.so.1.1 at runtime
  export PYTHON_CONFIGURE_OPTS="--enable-shared --with-openssl=${prefix} --with-openssl-rpath=auto"
  export LDFLAGS="-L${prefix}/lib -Wl,-rpath,${prefix}/lib ${LDFLAGS:-}"
  export CPPFLAGS="-I${prefix}/include ${CPPFLAGS:-}"
  export PKG_CONFIG_PATH="${prefix}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
  export LD_LIBRARY_PATH="${prefix}/lib:${LD_LIBRARY_PATH:-}"
  export PATH="${prefix}/bin:${PATH}"
}

elda_openssl_fix_symlinks() {
  local prefix="$1"
  local lib="${prefix}/lib"
  [[ -d "$lib" ]] || return 0
  if [[ ! -e "${lib}/libssl.so" && -f "${lib}/libssl.so.1.1" ]]; then
    ln -sf libssl.so.1.1 "${lib}/libssl.so"
  fi
  if [[ ! -e "${lib}/libcrypto.so" && -f "${lib}/libcrypto.so.1.1" ]]; then
    ln -sf libcrypto.so.1.1 "${lib}/libcrypto.so"
  fi
}

elda_pyenv_python_has_ssl() {
  local ver="$1"
  local py="${PYENV_ROOT:-$HOME/.pyenv}/versions/${ver}/bin/python"
  [[ -x "$py" ]] || return 1
  "$py" -c "import ssl" 2>/dev/null
}

elda_pyenv_remove_broken_python() {
  local ver="$1"
  local root="${PYENV_ROOT:-$HOME/.pyenv}"
  local vdir="${root}/versions/${ver}"
  if [[ -d "$vdir" ]] && ! elda_pyenv_python_has_ssl "$ver"; then
    echo "==> Removing broken Python ${ver} (ssl module missing)..."
    rm -rf "$vdir"
    if command -v pyenv &>/dev/null; then
      pyenv rehash 2>/dev/null || true
    fi
  fi
}

elda_ensure_pyenv() {
  export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"

  if [[ -x "$PYENV_ROOT/bin/pyenv" ]]; then
    echo "==> pyenv already installed: $("$PYENV_ROOT/bin/pyenv" --version)"
    export PATH="$PYENV_ROOT/bin:$PATH"
    return 0
  fi

  if [[ -d "$PYENV_ROOT" ]]; then
    echo "==> Removing incomplete ~/.pyenv (bin/pyenv missing)..."
    rm -rf "$PYENV_ROOT"
  fi

  echo "==> Installing pyenv (CN mirror)"
  local tmp
  tmp="$(mktemp)"
  if ! elda_download_first "$tmp" "${ELDA_PYENV_INSTALLER_URLS[@]}"; then
    rm -f "$tmp"
    echo "ERROR: could not download pyenv installer" >&2
    return 1
  fi
  bash "$tmp"
  rm -f "$tmp"

  if [[ ! -x "$PYENV_ROOT/bin/pyenv" ]]; then
    echo "ERROR: pyenv install failed — $PYENV_ROOT/bin/pyenv not found" >&2
    return 1
  fi
  export PATH="$PYENV_ROOT/bin:$PATH"
  echo "==> pyenv installed: $(pyenv --version)"
}

elda_prefetch_python_for_pyenv() {
  local cache="${PYENV_ROOT:-$HOME/.pyenv}/cache"
  local dest="$cache/${ELDA_PYTHON_TARBALL}"
  mkdir -p "$cache"
  if elda_is_valid_python_tarball "$dest" 2>/dev/null; then
    echo "==> Python source already cached: $dest ($(du -h "$dest" | cut -f1))"
    return 0
  fi
  rm -f "$dest"
  echo "==> Downloading ${ELDA_PYTHON_TARBALL} (~19 MB, CN mirror, progress bar below)"
  if ! elda_download_with_progress "$dest" "${ELDA_PYTHON_TARBALL_URLS[@]}"; then
    echo "ERROR: could not download Python ${ELDA_PYTHON_VERSION} source" >&2
    echo "  Tried: ${ELDA_PYTHON_TARBALL_URLS[*]}" >&2
    return 1
  fi
}

elda_pip_install_elda_packages() {
  local root="$1"
  echo "==> Installing ELDA CLI (editable, pip mirror)"
  elda_configure_pip_cn
  pip install --upgrade pip setuptools wheel

  elda_pip_preinstall_xenial_wheels

  pip install --prefer-binary -e "${root}/elda[dev,pdf]" -e "${root}/elda-api"

  if elda_is_xenial; then
    echo ""
    echo "==> PDF ingest on Ubuntu 16.04: PyMuPDF + pdftotext (MinerU skipped — needs glibc >= 2.28)"
    if command -v pdftotext &>/dev/null; then
      echo "    pdftotext: $(command -v pdftotext)"
    else
      echo "    WARN: pdftotext missing — run: sudo apt-get install -y poppler-utils"
    fi
    if python -c "import fitz" 2>/dev/null; then
      echo "    pymupdf: OK"
    else
      echo "    WARN: pymupdf import failed"
    fi
    return 0
  fi

  echo "==> Installing MinerU (PDF ingest, optional)"
  if pip install --prefer-binary "mineru[core]>=3.4.0"; then
    echo "==> MinerU installed"
  else
    echo "WARN: MinerU install failed — elda ingest PDF will not work until fixed" >&2
  fi
}

elda_ensure_pyenv_in_shell() {
  local marker="# ELDA / pyenv"
  local bashrc="$HOME/.bashrc"
  if [[ -f "$bashrc" ]] && grep -qF "$marker" "$bashrc"; then
    return 0
  fi
  echo "==> Adding pyenv to $bashrc (open a new terminal or: source ~/.bashrc)"
  {
    echo ""
    elda_pyenv_shell_snippet
  } >>"$bashrc"
}
