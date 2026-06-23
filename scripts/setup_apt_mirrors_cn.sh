#!/usr/bin/env bash
# Configure apt to use China mirrors. Ubuntu 16.04 xenial → old-releases (per-vendor paths).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/cn_mirrors.sh
source "$SCRIPT_DIR/lib/cn_mirrors.sh"

CODENAME="$(elda_codename)"
echo "==> ELDA apt mirror setup (codename=$CODENAME)"

elda_apt_setup_cn "$CODENAME"
