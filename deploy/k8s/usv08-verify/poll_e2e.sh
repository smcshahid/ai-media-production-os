#!/usr/bin/env bash
# Poll US-V08 E2E progress on Olares.
set -uo pipefail
LOG="${1:-/tmp/usv08-evidence/e2e-olares.log}"
SUMMARY="/tmp/usv08-evidence/summary.txt"
if [ -f "$SUMMARY" ]; then
  echo "=== SUMMARY ==="
  cat "$SUMMARY"
  exit 0
fi
tail -30 "$LOG" 2>/dev/null || echo "No log yet at $LOG"
pgrep -af verify_usv08_e2e || echo "E2E process not running"
