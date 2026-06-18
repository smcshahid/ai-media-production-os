#!/usr/bin/env bash
# Supplemental PATH C1 attestation (single episode, 3 characters).
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv08-c1-evidence}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

source /tmp/verify_usv08_e2e.sh 2>/dev/null || true

# If sourced, functions exist; else copy minimal run
if ! declare -f run_character_path >/dev/null; then
  echo "ERROR: verify_usv08_e2e.sh functions required at /tmp/verify_usv08_e2e.sh"
  exit 1
fi

exec 9>"$EVID/.c1.lock"
flock -n 9 || { echo "FAIL lock held"; exit 1; }

log "US-V08 PATH C1 supplemental start"
cancel_active_runs
cleanup_project_characters

RESULT=$(run_character_path C1 1 3 "US-V08 Path C1 Supplement Episode") || exit 1
echo "PATH_C1=$RESULT"
echo "PASS PATH C1 supplemental"
