#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE_URL="https://nvo.hatchable.site"
AGENT_ID="${NOVA_TERMUX_AGENT_ID:-termux-main}"
if [ -z "${NOVA_TERMUX_BRIDGE_TOKEN:-}" ]; then
  read -rsp "Nova Termux bridge token: " NOVA_TERMUX_BRIDGE_TOKEN
  echo
fi
WORKSPACE="${NOVA_TERMUX_WORKSPACE:-$HOME}"
API="$BASE_URL/api/nova-termux-bridge"
mkdir -p "$WORKSPACE/.nova"
echo "Nova Termux bridge online: $AGENT_ID"
while true; do
  curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json" -d "{\"action\":\"heartbeat\",\"agent_id\":\"$AGENT_ID\",\"device_name\":\"Android Termux\",\"workspace\":\"$WORKSPACE\",\"capabilities\":{\"shell\":true,\"python\":true,\"node\":true,\"git\":true,\"curl\":true,\"workspace_only\":true}}" >/dev/null || true
  job="$(curl -fsS --max-time 15 "$API?agent_id=$AGENT_ID" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" || true)"
  job_id="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("id") or "")' 2>/dev/null || true)"
  if [ -n "$job_id" ]; then
    command="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("command") or "")' 2>/dev/null || true)"
    cwd="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("cwd") or "")' 2>/dev/null || true)"
    timeout_s="$(printf '%s' "$job" | python -c 'import json,sys; print((json.load(sys.stdin).get("job") or {}).get("timeout_seconds") or 60)' 2>/dev/null || echo 60)"
    case "$cwd" in ""|"$WORKSPACE"|"$WORKSPACE"/*) ;; *) cwd="$WORKSPACE" ;; esac
    case "$command" in
      cd\ *|pwd|ls\ *|find\ *|git\ *|python\ *|python3\ *|node\ *|npm\ *|npx\ *|curl\ *|grep\ *|sed\ *|awk\ *|cat\ *|head\ *|tail\ *|mkdir\ *|cp\ *|mv\ *|rm\ *|chmod\ *|bash\ *|sh\ *) ;;
      *) command="" ;;
    esac
    if [ -n "$command" ]; then
      out_file="$WORKSPACE/.nova/job-$job_id.out"; err_file="$WORKSPACE/.nova/job-$job_id.err"
      (cd "$cwd" && timeout "$timeout_s" bash -lc "$command") >"$out_file" 2>"$err_file" || rc=$?
      rc="${rc:-0}"
      stdout="$(python -c 'import json; print(json.dumps(open("'$out_file'",errors="replace").read()[-12000:]))')"
      stderr="$(python -c 'import json; print(json.dumps(open("'$err_file'",errors="replace").read()[-12000:]))')"
      curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json" -d "{\"action\":\"complete\",\"agent_id\":\"$AGENT_ID\",\"job_id\":$job_id,\"exit_code\":$rc,\"stdout\":$stdout,\"stderr\":$stderr}" >/dev/null || true
      rm -f "$out_file" "$err_file"
    else
      curl -fsS --max-time 15 -X POST "$API" -H "Authorization: Bearer $NOVA_TERMUX_BRIDGE_TOKEN" -H "Content-Type: application/json" -d "{\"action\":\"complete\",\"agent_id\":\"$AGENT_ID\",\"job_id\":$job_id,\"exit_code\":126,\"stdout\":\"\",\"stderr\":\"command blocked by Termux bridge policy\"}" >/dev/null || true
    fi
  fi
  sleep 5
done
