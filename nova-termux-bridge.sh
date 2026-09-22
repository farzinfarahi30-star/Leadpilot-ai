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

json_get(){
  python - "$1" <<'PY'
import json,sys
d=json.load(sys.stdin); k=sys.argv[1]; v=d.get(k,'')
print(json.dumps(v) if isinstance(v,(dict,list)) else v)
PY
}
json_arg(){
  python - "$1" "$2" <<'PY'
import json,sys
d=json.loads(sys.argv[1]); v=d.get(sys.argv[2],'')
print(v if isinstance(v,str) else json.dumps(v,separators=(',',':')))
PY
}
safe_path(){
  local rel="$1" root resolved
  case "$rel" in ""|/*|*..*) return 1;; esac
  root="$(realpath -m -- "$WORKSPACE")"
  resolved="$(realpath -m -- "$WORKSPACE/$rel")"
  case "$resolved" in "$root"|"$root"/*) printf '%s' "$resolved";; *) return 1;; esac
}

install(){
  pkg update -y
  pkg install -y curl python coreutils git
  command -v timeout >/dev/null || { echo "timeout is required"; exit 1; }
  echo "Open $BASE_URL/nova-termux.html and obtain the one-time 8-character pairing code."
  read -rp "Pairing code: " PAIR_CODE
  result="$(curl -fsS --max-time 15 -X POST "$PAIR_API" -H "Content-Type: application/json" -d "{"agent_id":"$AGENT_ID","code":"$PAIR_CODE","device_name":"Android Termux","workspace":"$WORKSPACE"}")" || { echo "Pairing request failed."; exit 1; }
  token="$(printf '%s' "$result" | json_get token 2>/dev/null || true)"
  [ -n "$token" ] || { echo "Pairing failed."; printf '%s\n' "$result"; exit 1; }
  printf 'NOVA_TERMUX_BRIDGE_TOKEN=%s\n' "$token" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  cp "$0" "$ROOT/bridge.sh"
  chmod 700 "$ROOT/bridge.sh"
  mkdir -p "$HOME/.termux/boot"
  printf '%s\n' "#!/data/data/com.termux/files/usr/bin/bash" "exec \"$ROOT/bridge.sh\" start" > "$HOME/.termux/boot/nova-termux-start"
  chmod 700 "$HOME/.termux/boot/nova-termux-start"
  echo "Paired successfully."
  start
}

start(){
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then echo "Nova Termux bridge already running."; exit 0; fi
  [ -f "$ENV_FILE" ] || { echo "Not paired. Run: $0 install"; exit 1; }
  . "$ENV_FILE"
  command -v termux-wake-lock >/dev/null && termux-wake-lock || true
  nohup "$ROOT/bridge.sh" daemon >"$ROOT/bridge.log" 2>&1 &
  echo $! > "$PID_FILE"
  echo "Nova Termux bridge started."
}

stop(){
  if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; rm -f "$PID_FILE"; fi
  echo "Nova Termux bridge stopped."
}

status(){
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then echo "Nova Termux bridge: RUNNING"; else echo "Nova Termux bridge: STOPPED"; fi
  [ -f "$ENV_FILE" ] && echo "Pairing: configured" || echo "Pairing: not configured"
}

daemon(){
  . "$ENV_FILE"
  trap 'rm -f "$PID_FILE"' EXIT
  echo $$ > "$PID_FILE"
  while true; do
    curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json" -d "{"action":"heartbeat","agent_id":"$AGENT_ID","device_name":"Android Termux","workspace":"$WORKSPACE","capabilities":{"structured_operations":true,"workspace_only":true,"python":true,"node":true,"git":true,"boot_autostart":true}}" >/dev/null || true
    job="$(curl -fsS --max-time 15 "$API?agent_id=$AGENT_ID" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" || true)"
    job_id="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("id") or "")' 2>/dev/null || true)"
    if [ -n "$job_id" ]; then
      j="$(printf '%s' "$job" | python -c 'import json,sys; print(json.dumps((json.load(sys.stdin).get("job") or {}),separators=(",",":")))' 2>/dev/null || echo '{}')"
      op="$(printf '%s' "$j" | json_get operation 2>/dev/null || true)"
      args="$(printf '%s' "$j" | json_get args_json 2>/dev/null || echo '{}')"
      timeout_s="$(printf '%s' "$j" | json_get timeout_seconds 2>/dev/null || echo 60)"
      rc=0; out=""; err=""; target=""
      path="$(printf '%s' "$args" | json_get path 2>/dev/null || true)"
      if [ -n "$path" ]; then target="$(safe_path "$path")" || { rc=126; err="path outside workspace policy"; }; fi
      if [ "$rc" -eq 0 ]; then
        case "$op" in
          pwd) out="$WORKSPACE" ;;
          ls) out="$(ls -la "${target:-$WORKSPACE}")" ;;
          git_status) out="$(git -C "$WORKSPACE" status --short)" ;;
          git_diff) out="$(git -C "$WORKSPACE" diff -- "${path:-.}")" ;;
          git_log) out="$(git -C "$WORKSPACE" log -20 --oneline)" ;;
          git_pull) out="$(git -C "$WORKSPACE" pull --ff-only)" ;;
          node_file) out="$(timeout "$timeout_s" node "$target")" ;;
          python_file) out="$(timeout "$timeout_s" python "$target")" ;;
          npm_test) out="$(cd "$WORKSPACE" && timeout "$timeout_s" npm test -- --if-present)" ;;
          npm_lint) out="$(cd "$WORKSPACE" && timeout "$timeout_s" npm run lint --if-present)" ;;
          npm_build) out="$(cd "$WORKSPACE" && timeout "$timeout_s" npm run build --if-present)" ;;
          read_file) out="$(cat "$target")" ;;
          write_file)
            content="$(printf '%s' "$args" | json_get content 2>/dev/null || true)"
            [ -n "$path" ] && [ -n "$target" ] || { rc=126; err="invalid write target"; }
            if [ "$rc" -eq 0 ]; then mkdir -p "$(dirname "$target")"; printf '%s' "$content" > "$target"; out="wrote $path"; fi
            ;;
          *) rc=126; err="operation blocked by structured Termux policy" ;;
        esac
      fi
      payload_stdout="$(python -c 'import json,sys; print(json.dumps(sys.stdin.read()[-12000:]))' <<<"$out")"
      payload_stderr="$(python -c 'import json,sys; print(json.dumps(sys.stdin.read()[-12000:]))' <<<"$err")"
      curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json" -d "{"action":"complete","agent_id":"$AGENT_ID","job_id":$job_id,"exit_code":$rc,"stdout":$payload_stdout,"stderr":$payload_stderr}" >/dev/null || true
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