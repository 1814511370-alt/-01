#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_PATH="${BIN_PATH:-$SCRIPT_DIR/daidai-linux-amd64}"
PID_FILE="${PID_FILE:-/tmp/automation-panel.pid}"
BASE_URL="${BASE_URL:-http://127.0.0.1:5701/}"

find_running_pid() {
  local pid
  pid="$(pgrep -f "$BIN_PATH" | head -n 1 || true)"
  printf '%s' "$pid"
}

pid="$(find_running_pid)"
if [ -n "$pid" ]; then
  printf 'automation-panel: running (PID %s)\n' "$pid"
  printf '%s' "$pid" > "$PID_FILE"
else
  if [ -f "$PID_FILE" ]; then
    printf 'automation-panel: stopped (last recorded PID %s)\n' "$(cat "$PID_FILE")"
  else
    printf 'automation-panel: stopped (pid file missing: %s)\n' "$PID_FILE"
  fi
fi

code="$(curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' "$BASE_URL" || true)"
if [ -z "$code" ] || [ "$code" = "000" ]; then
  printf 'local root: unavailable (%s)\n' "$BASE_URL"
  exit 0
fi

printf 'local root: HTTP %s (%s)\n' "$code" "$BASE_URL"
