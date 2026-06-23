#!/usr/bin/env bash
set -euo pipefail

DEMO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "${DEMO_ROOT}/../.." && pwd)"
VENDOR_KERNEL="${DEMO_ROOT}/vendor/kernel"
DEMO_BRANCH="${ELDA_DEMO_GIT_BRANCH:-elda/icm20608-imx6ull}"
CROSS_COMPILE="${CROSS_COMPILE:-arm-linux-gnueabihf-}"
BOARD_DTS_NAME="imx6ull-elda-demo.dts"
BOARD_DTS_REL="arch/arm/boot/dts/${BOARD_DTS_NAME}"

echo "==> demo bootstrap: ${DEMO_ROOT}"

export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
export PATH="/usr/local/bin:$PYENV_ROOT/bin:$PATH"
[[ -x "$PYENV_ROOT/bin/pyenv" ]] && eval "$("$PYENV_ROOT/bin/pyenv" init -)" 2>/dev/null || true

if ! command -v elda &>/dev/null; then
  echo "ERROR: elda CLI not found; run: bash ${REPO_ROOT}/scripts/install_deps_ubuntu1604.sh"
  exit 1
fi

mkdir -p \
  "${DEMO_ROOT}/deploy/tftp" \
  "${DEMO_ROOT}/deploy/nfs/root/drivers" \
  "${DEMO_ROOT}/deploy/nfs/root/tests" \
  "${DEMO_ROOT}/docs" \
  "${DEMO_ROOT}/workspace/soc" \
  "${DEMO_ROOT}/workspace/peripherals/icm20608_0" \
  "${DEMO_ROOT}/output/patches" \
  "${DEMO_ROOT}/output/logs" \
  "${DEMO_ROOT}/reports" \
  "${DEMO_ROOT}/captures"
touch "${DEMO_ROOT}/deploy/nfs/root/drivers/.gitkeep"
touch "${DEMO_ROOT}/deploy/nfs/root/tests/.gitkeep"

if [[ ! -f "${DEMO_ROOT}/docs/icm20608.pdf" ]]; then
  echo "WARN: missing ${DEMO_ROOT}/docs/icm20608.pdf (required for elda ingest)"
fi

if [[ ! -d "${VENDOR_KERNEL}/.git" ]] || [[ ! -f "${VENDOR_KERNEL}/Makefile" ]]; then
  echo "==> kernel tree missing; running fetch_kernel.sh"
  bash "${DEMO_ROOT}/scripts/fetch_kernel.sh"
fi

NEED_APT=()
for pkg in gcc-arm-linux-gnueabihf bc bison flex libssl-dev libncurses5-dev libncursesw5-dev u-boot-tools; do
  dpkg -s "$pkg" &>/dev/null || NEED_APT+=("$pkg")
done
if [[ ${#NEED_APT[@]} -gt 0 ]]; then
  sudo apt-get update -qq
  sudo apt-get install -y "${NEED_APT[@]}"
fi

echo "==> install board DTS and kernel configuration"
cp "${DEMO_ROOT}/board/${BOARD_DTS_NAME}" "${VENDOR_KERNEL}/${BOARD_DTS_REL}"
MAKEFILE="${VENDOR_KERNEL}/arch/arm/boot/dts/Makefile"
if [[ -f "$MAKEFILE" ]] && ! grep -q 'imx6ull-elda-demo.dtb' "$MAKEFILE"; then
  sed -i '/imx6ull.*\.dtb/s/$/ \\\n\timx6ull-elda-demo.dtb/' "$MAKEFILE" 2>/dev/null || \
    echo 'dtb-$(CONFIG_SOC_IMX6UL) += imx6ull-elda-demo.dtb' >> "$MAKEFILE"
fi

git -C "$VENDOR_KERNEL" checkout -B "$DEMO_BRANCH" -q

cp "${DEMO_ROOT}/board/kernel.config.fragment" "${VENDOR_KERNEL}/.config"
make -C "$VENDOR_KERNEL" ARCH=arm CROSS_COMPILE="$CROSS_COMPILE" olddefconfig -s
git -C "$VENDOR_KERNEL" add -A
git -C "$VENDOR_KERNEL" commit -q -m "elda demo: ${BOARD_DTS_NAME} and kernel config" || true

cd "$DEMO_ROOT"
elda doctor || true

echo "==> bootstrap complete"
echo "    kernel:  ${VENDOR_KERNEL}"
echo "    config:  ${DEMO_ROOT}/elda.yaml"
echo "    next:    elda executor start  (terminal A)"
echo "             elda ingest && elda verify workspace  (terminal B)"
