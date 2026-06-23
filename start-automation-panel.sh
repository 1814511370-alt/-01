#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_PATH="${BIN_PATH:-$SCRIPT_DIR/daidai-linux-amd64}"
PID_FILE="${PID_FILE:-/tmp/automation-panel.pid}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/data/logs/automation-panel-managed.log}"
BASE_URL="${BASE_URL:-http://127.0.0.1:5701/}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-20}"
PANEL_TZ="${PANEL_TZ:-Asia/Shanghai}"

find_running_pid() {
  local pid
  pid="$(pgrep -f "$BIN_PATH" | head -n 1 || true)"
  printf '%s' "$pid"
}

wait_for_http_ready() {
  local url="$1"
  local timeout_seconds="$2"
  local started_at
  local code

  started_at="$(date +%s)"
  while true; do
    code="$(curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' "$url" || true)"
    if [ "$code" = "200" ]; then
      printf 'HTTP ready: %s (%s)\n' "$code" "$url"
      return 0
    fi

    if [ $(( $(date +%s) - started_at )) -ge "$timeout_seconds" ]; then
      printf 'Timed out waiting for HTTP ready: %s (%s)\n' "$code" "$url"
      return 1
    fi

    sleep 1
  done
}

mkdir -p "$SCRIPT_DIR/data/logs"

running_pid="$(find_running_pid)"
if [ -n "$running_pid" ]; then
  printf '%s' "$running_pid" > "$PID_FILE"
  printf 'automation-panel already running with PID %s\n' "$running_pid"
  printf 'Panel URL: %s\n' "$BASE_URL"
  exit 0
fi

nohup env TZ="$PANEL_TZ" "$BIN_PATH" >>"$LOG_FILE" 2>&1 &
sleep 1

running_pid="$(find_running_pid)"
if [ -z "$running_pid" ]; then
  printf 'Failed to confirm automation-panel startup\n'
  exit 1
fi

printf '%s' "$running_pid" > "$PID_FILE"
wait_for_http_ready "$BASE_URL" "$STARTUP_TIMEOUT_SECONDS"

printf 'Started automation-panel with PID %s\n' "$running_pid"
printf 'Panel URL: %s\n' "$BASE_URL"
printf 'Panel TZ: %s\n' "$PANEL_TZ"
