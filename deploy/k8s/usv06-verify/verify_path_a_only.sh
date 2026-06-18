#!/usr/bin/env bash
set -uo pipefail
EVID="${EVID_DIR:-/tmp/usv06-evidence-path-a}"
mkdir -p "$EVID"
export EVID_DIR="$EVID"
source /tmp/verify_usv06_e2e.sh
run_path A 1
exit $?
