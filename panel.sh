#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  printf 'Usage: %s {start|stop|restart|status|check|md-check}\n' "$0"
  printf '\n'
  printf 'Commands:\n'
  printf '  start     Start automation panel\n'
  printf '  stop      Stop automation panel\n'
  printf '  restart   Restart automation panel\n'
  printf '  status    Show service status\n'
  printf '  check     Run task configuration doctor\n'
  printf '  md-check  Check and run md keepalive tasks\n'
}

command_name="${1:-}"

case "$command_name" in
  start)
    "$SCRIPT_DIR/start-automation-panel.sh"
    ;;
  stop)
    "$SCRIPT_DIR/stop-automation-panel.sh"
    ;;
  restart)
    "$SCRIPT_DIR/restart-automation-panel.sh"
    ;;
  status)
    "$SCRIPT_DIR/status-automation-panel.sh"
    ;;
  check)
    "$SCRIPT_DIR/check-panel-tasks.py"
    ;;
  md-check)
    shift || true
    "$SCRIPT_DIR/check-md-keepalive.py" "$@"
    ;;
  -h|--help|help|'')
    usage
    ;;
  *)
    printf 'Unknown command: %s\n\n' "$command_name" >&2
    usage >&2
    exit 2
    ;;
esac
