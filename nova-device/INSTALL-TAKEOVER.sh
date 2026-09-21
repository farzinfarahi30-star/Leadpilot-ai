#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROFILE="${NOVA_TERMUX_PROFILE:-developer}"
REPO="${NOVA_PROJECT_ROOT:-$HOME/Leadpilot-ai}"

if ! command -v pkg >/dev/null 2>&1; then
  echo "This installer must run inside Termux." >&2
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  pkg install -y git
fi

if [ ! -d "$REPO/.git" ]; then
  if [ -e "$REPO" ]; then
    echo "Target exists but is not a Git repository: $REPO" >&2
    exit 2
  fi
  mkdir -p "$(dirname "$REPO")"
  git clone --depth=1 https://github.com/farzinfarahi30-star/Leadpilot-ai.git "$REPO"
fi

if [ ! -f "$REPO/nova-device/install-termux.sh" ]; then
  echo "Nova repository bootstrap failed: $REPO/nova-device/install-termux.sh is missing." >&2
  exit 2
fi

export NOVA_PROJECT_ROOT="$REPO"
export NOVA_TERMUX_PROFILE="$PROFILE"

cd "$REPO/nova-device"
chmod +x ./install-termux.sh
./install-termux.sh

mkdir -p "$HOME/.termux/boot"
cp -f "$REPO/nova-device/termux/boot/00-nova-supervisor" "$HOME/.termux/boot/00-nova-supervisor"
chmod +x "$HOME/.termux/boot/00-nova-supervisor"

mkdir -p "$REPO/.nova-device"
cat > "$REPO/.nova-device/supervisor.env" <<EOF
NOVA_PROJECT_ROOT=$REPO
NOVA_SUPERVISE_RUNTIME=true
NOVA_SUPERVISE_DESKTOP_COMMANDER=true
NOVA_DEVICE_AUTO_PROVISION=true
NOVA_TERMUX_PROFILE=$PROFILE
EOF

if command -v pm >/dev/null 2>&1 && ! pm list packages 2>/dev/null | grep -q '^package:com.termux.boot$'; then
  echo "WARNING: Termux:Boot is not installed; Nova will run now but cannot auto-start after reboot."
fi

echo "NOVA_TAKEOVER_READY"
echo "Boot supervisor: $HOME/.termux/boot/00-nova-supervisor"
echo "State file: $REPO/.nova-device/supervisor.json"

exec node "$REPO/nova-device/src/supervisor.mjs"
