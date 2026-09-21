#!/data/data/com.termux/files/usr/bin/bash
set -eu

PROFILE="${NOVA_TERMUX_PROFILE:-developer}"
REPO="${NOVA_PROJECT_ROOT:-$HOME/Leadpilot-ai}"

if [ ! -d "$REPO/.git" ]; then
  if command -v git >/dev/null 2>&1; then
    mkdir -p "$REPO"
  else
    pkg install -y git
    mkdir -p "$REPO"
  fi
fi

if [ ! -f "$REPO/package.json" ] && [ -f "$HOME/Leadpilot-ai/nova-device/package.json" ]; then
  REPO="$HOME/Leadpilot-ai"
fi

if [ ! -f "$REPO/nova-device/install-termux.sh" ]; then
  echo "Nova repo not found at $REPO" >&2
  echo "Clone farzinfarahi30-star/Leadpilot-ai into $REPO, then rerun this installer." >&2
  exit 2
fi

export NOVA_PROJECT_ROOT="$REPO"
export NOVA_TERMUX_PROFILE="$PROFILE"
cd "$REPO/nova-device"
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

echo "NOVA_TAKEOVER_READY"
echo "Boot supervisor: $HOME/.termux/boot/00-nova-supervisor"
echo "State file: $REPO/.nova-device/supervisor.json"

exec node "$REPO/nova-device/src/supervisor.mjs"
