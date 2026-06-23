#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/stop-automation-panel.sh"
"$SCRIPT_DIR/start-automation-panel.sh"
"$SCRIPT_DIR/status-automation-panel.sh"
