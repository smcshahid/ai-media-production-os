#!/usr/bin/env bash
# Poll US-V07 E2E progress on Olares.
set -uo pipefail
LOG=/tmp/usv07-evidence/e2e-olares.log
for i in $(seq 1 120); do
  if ! pgrep -f verify_usv07_e2e.sh >/dev/null 2>&1; then
    echo "E2E finished"
    tail -40 "$LOG"
    grep -E '^(PASS|FAIL|DONE)' "$LOG" | tail -20
    exit 0
  fi
  echo "--- poll $i $(date -Iseconds) ---"
  tail -4 "$LOG"
  sleep 30
done
echo "Still running after 60 minutes"
tail -20 "$LOG"
