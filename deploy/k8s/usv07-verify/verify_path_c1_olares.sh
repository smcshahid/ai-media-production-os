#!/usr/bin/env bash
# Supplemental PATH C1 acceptance (re-run after orphan cleanup). Sources main E2E helpers.
set -uo pipefail
EVID="${EVID_DIR:-/tmp/usv07-evidence-c1}"
mkdir -p "$EVID"
export EVID_DIR="$EVID"

# shellcheck source=/dev/null
source /tmp/verify_usv07_e2e.sh

log "US-V07 PATH C1 supplement start PROJECT=$PROJECT"
cancel_active_runs || true

PATH_C1_RESULT=""
FAIL=0
PATH_C1_RESULT=$(run_episode_path C1 1 "US-V07 Path C Episode 1 supplement") || FAIL=1

{
  echo "PATH_C1=$PATH_C1_RESULT"
  echo "FAIL=$FAIL"
} > "$EVID/summary-c1.txt"

log "DONE PATH C1 supplement FAIL=$FAIL"
exit $FAIL
