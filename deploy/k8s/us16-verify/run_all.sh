#!/usr/bin/env bash
# Cancel stale run, then run full US-16 Olares verification.
set -euo pipefail
STALE_RUN="${STALE_RUN:-ad45f3a7-e772-437b-be00-c62a9121cec1}"
chmod +x /tmp/cancel_stale_run.sh /tmp/verify_us16.sh /tmp/run_remote.sh
bash /tmp/cancel_stale_run.sh "$STALE_RUN"
bash /tmp/run_remote.sh
