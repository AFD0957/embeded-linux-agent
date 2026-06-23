#!/usr/bin/env bash
set -euo pipefail

DEMO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR_KERNEL="${DEMO_ROOT}/vendor/kernel"
KERNEL_BRANCH="${ELDA_KERNEL_BRANCH:-imx_4.1.15_2.0.0_ga}"

if [[ -d "${VENDOR_KERNEL}/.git" ]] && [[ -f "${VENDOR_KERNEL}/Makefile" ]]; then
  echo "kernel tree already present: ${VENDOR_KERNEL}"
  exit 0
fi

echo "==> fetch NXP linux-imx into ${VENDOR_KERNEL}"
mkdir -p "${VENDOR_KERNEL}"
rm -f "${VENDOR_KERNEL}/.gitkeep"

clone_into() {
  local url="$1"
  local tmp
  tmp="$(mktemp -d)"
  echo "trying: ${url} (branch ${KERNEL_BRANCH})"
  if git clone --depth 1 -b "${KERNEL_BRANCH}" "${url}" "${tmp}/linux-imx"; then
    shopt -s dotglob nullglob
    rm -rf "${VENDOR_KERNEL:?}"/*
    mv "${tmp}/linux-imx"/* "${VENDOR_KERNEL}/"
    rm -rf "${tmp}"
    return 0
  fi
  rm -rf "${tmp}"
  return 1
}

URLS=(
  "https://github.com/nxp-imx/linux-imx.git"
  "https://mirror.ghproxy.com/https://github.com/nxp-imx/linux-imx.git"
  "https://ghfast.top/https://github.com/nxp-imx/linux-imx.git"
)
for u in "${URLS[@]}"; do
  if clone_into "$u"; then
    echo "==> kernel ready at ${VENDOR_KERNEL}"
    exit 0
  fi
done

echo "ERROR: git clone failed for all URLs" >&2
echo "Manual:" >&2
echo "  git clone --depth 1 -b ${KERNEL_BRANCH} https://github.com/nxp-imx/linux-imx.git ${VENDOR_KERNEL}" >&2
exit 1
