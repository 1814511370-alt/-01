#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

printf 'Current environment has no systemd init; using session-level autostart helper.\n'
"$SCRIPT_DIR/start-automation-panel.sh"
