#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE_URL="https://nvo.hatchable.site"
AGENT_ID="${NOVA_TERMUX_AGENT_ID:-termux-main}"
WORKSPACE="${NOVA_TERMUX_WORKSPACE:-$HOME}"
ROOT="$WORKSPACE/.nova"
API="$BASE_URL/api/nova-termux-bridge"
PAIR_API="$BASE_URL/api/nova-termux-pair"
ENV_FILE="$ROOT/bridge.env"
PID_FILE="$ROOT/bridge.pid"
mkdir -p "$ROOT"
umask 077

install(){
  pkg update -y
  pkg install -y curl python coreutils git
  command -v timeout >/dev/null || { echo "timeout is required"; exit 1; }
  echo
  echo "Open $BASE_URL/nova-termux.html in your browser while signed into NVO."
  read -rp "Enter the 8-character pairing code: " PAIR_CODE
  result="$(curl -fsS --max-time 15 -X POST "$PAIR_API" -H "Content-Type: application/json"     -d "{\"agent_id\":\"$AGENT_ID\",\"code\":\"$PAIR_CODE\",\"device_name\":\"Android Termux\",\"workspace\":\"$WORKSPACE\"}")"
  token="$(printf '%s' "$result" | python -c 'import json,sys; print(json.load(sys.stdin).get("token",""))' 2>/dev/null || true)"
  [ -n "$token" ] || { echo "Pairing failed."; printf '%s\n' "$result"; exit 1; }
  printf 'NOVA_TERMUX_BRIDGE_TOKEN=%s\n' "$token" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  cp "$0" "$ROOT/bridge.sh"
  chmod 700 "$ROOT/bridge.sh"
  mkdir -p "$HOME/.termux/boot"
  cat > "$HOME/.termux/boot/nova-termux-start" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
exec "$ROOT/bridge.sh" start
EOF
  chmod 700 "$HOME/.termux/boot/nova-termux-start"
  echo "Paired. Starting Nova Termux bridge."
  start
}

start(){
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Nova Termux bridge already running (PID $(cat "$PID_FILE"))."
    exit 0
  fi
  [ -f "$ENV_FILE" ] || { echo "Not paired. Run: $0 install"; exit 1; }
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  command -v termux-wake-lock >/dev/null && termux-wake-lock || true
  nohup "$ROOT/bridge.sh" daemon >"$ROOT/bridge.log" 2>&1 &
  echo $! > "$PID_FILE"
  echo "Nova Termux bridge started (PID $!)."
}

stop(){
  if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; rm -f "$PID_FILE"; fi
  echo "Nova Termux bridge stopped."
}

status(){
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Nova Termux bridge: RUNNING (PID $(cat "$PID_FILE"))"
  else
    echo "Nova Termux bridge: STOPPED"
  fi
  if [ -f "$ENV_FILE" ]; then
    echo "Pairing: configured"
  else
    echo "Pairing: not configured"
  fi
}

daemon(){
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  trap 'rm -f "$PID_FILE"' EXIT
  echo $$ > "$PID_FILE"
  echo "Nova Termux daemon online: $AGENT_ID"
  while true; do
    curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json"       -d "{\"action\":\"heartbeat\",\"agent_id\":\"$AGENT_ID\",\"device_name\":\"Android Termux\",\"workspace\":\"$WORKSPACE\",\"capabilities\":{\"shell\":true,\"python\":true,\"node\":true,\"git\":true,\"curl\":true,\"workspace_only\":true,\"boot_autostart\":true}}" >/dev/null || true
    job="$(curl -fsS --max-time 15 "$API?agent_id=$AGENT_ID" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" || true)"
    job_id="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("id") or "")' 2>/dev/null || true)"
    if [ -n "$job_id" ]; then
      command="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("command") or "")' 2>/dev/null || true)"
      cwd="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("cwd") or "")' 2>/dev/null || true)"
      timeout_s="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("timeout_seconds") or 60)' 2>/dev/null || echo 60)"
      case "$cwd" in ""|"$WORKSPACE"|"$WORKSPACE"/*) ;; *) cwd="$WORKSPACE" ;; esac
      case "$command" in
        *"sudo "*|*" su "*|*"termux-chroot"*|*"rm -rf /"*|*"../"*|*/proc/*|*/sys/*|*/dev/*) command="" ;;
      esac
      case "$command" in
        cd\ *|pwd|ls*|find*|git*|python\ *|python3\ *|node\ *|npm\ *|npx\ *|curl\ *|grep*|sed*|awk*|cat*|head*|tail*|mkdir*|cp*|mv*|rm\ *|chmod\ *|bash\ *|sh\ *) ;;
        *) command="" ;;
      esac
      out_file="$ROOT/job-$job_id.out"; err_file="$ROOT/job-$job_id.err"
      if [ -n "$command" ]; then
        rc=0
        (cd "$cwd" && timeout "$timeout_s" bash -lc "$command") >"$out_file" 2>"$err_file" || rc=$?
        stdout="$(python -c 'import json; print(json.dumps(open("'$out_file'",errors="replace").read()[-12000:]))')"
        stderr="$(python -c 'import json; print(json.dumps(open("'$err_file'",errors="replace").read()[-12000:]))')"
      else
        rc=126
        stdout='""'
        stderr='"command blocked by Termux bridge policy"'
      fi
      curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json"         -d "{\"action\":\"complete\",\"agent_id\":\"$AGENT_ID\",\"job_id\":$job_id,\"exit_code\":$rc,\"stdout\":$stdout,\"stderr\":$stderr}" >/dev/null || true
      rm -f "$out_file" "$err_file"
    fi
    sleep 5
  done
}

case "${1:-install}" in
  install) install ;;
  start) start ;;
  stop) stop ;;
  status) status ;;
  daemon) daemon ;;
  *) echo "Usage: $0 {install|start|stop|status}"; exit 2 ;;
esac
