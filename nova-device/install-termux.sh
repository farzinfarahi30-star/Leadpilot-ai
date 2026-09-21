#!/data/data/com.termux/files/usr/bin/bash
set -eu
ROOT="$(cd "$(dirname "$0")" && pwd)"
PROFILE="${NOVA_TERMUX_PROFILE:-developer}"
export NOVA_DEVICE_ALLOWED_ROOTS="${NOVA_DEVICE_ALLOWED_ROOTS:-$HOME/Leadpilot-ai:$ROOT}"
printf '%s\n' "Nova Termux bootstrap: profile=$PROFILE"
pkg update -y
pkg upgrade -y
case "$PROFILE" in
  minimal) PKGS="git curl wget openssh ripgrep jq tar unzip zip" ;;
  developer) PKGS="git curl wget openssh ripgrep jq tar unzip zip python nodejs npm make clang cmake pkg-config rust golang perl ruby termux-api proot-distro" ;;
  build) PKGS="git curl wget openssh ripgrep jq tar unzip zip python nodejs npm make clang clang++ cmake pkg-config rust golang perl ruby php termux-api proot-distro" ;;
  *) echo "Unknown NOVA_TERMUX_PROFILE: $PROFILE" >&2; exit 2 ;;
esac
pkg install -y $PKGS
cd "$ROOT"
npm install --omit=dev
mkdir -p "$ROOT/.nova-device"
node "$ROOT/src/smoke.mjs"
printf '%s\n' "Nova Termux bootstrap complete."
