#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_PATH="${BIN_PATH:-$SCRIPT_DIR/daidai-linux-amd64}"
PID_FILE="${PID_FILE:-/tmp/automation-panel.pid}"
STOP_TIMEOUT_SECONDS="${STOP_TIMEOUT_SECONDS:-10}"

find_running_pid() {
  local pid
  pid="$(pgrep -f "$BIN_PATH" | head -n 1 || true)"
  printf '%s' "$pid"
}

pid="$(find_running_pid)"
if [ -z "$pid" ]; then
  printf 'automation-panel: already stopped\n'
  : > "$PID_FILE"
  exit 0
fi

kill "$pid"
started_at="$(date +%s)"
while kill -0 "$pid" 2>/dev/null; do
  if [ $(( $(date +%s) - started_at )) -ge "$STOP_TIMEOUT_SECONDS" ]; then
    kill -9 "$pid"
    printf 'automation-panel: force stopped PID %s\n' "$pid"
    break
  fi
  sleep 1
done

if ! kill -0 "$pid" 2>/dev/null; then
  printf 'automation-panel: stopped PID %s\n' "$pid"
fi

: > "$PID_FILE"
