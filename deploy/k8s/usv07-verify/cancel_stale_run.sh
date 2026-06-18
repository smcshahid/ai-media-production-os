#!/usr/bin/env bash
# Terminate a stale pipeline workflow and mark the run CANCELLED (US-V07 cleanup).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
RUN_ID="${1:?usage: cancel_stale_run.sh RUN_ID}"
WF="${2:-spark-pipeline-${RUN_ID}}"

echo "=== terminate workflow $WF ==="
$K exec deploy/temporal -n "$NS" -- tctl --address temporal:7233 workflow terminate \
  -w "$WF" -r "US-V07 verification cleanup" 2>&1 || echo "(terminate skipped)"

echo "=== mark run CANCELLED ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$(
  $K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d
)" psql -U aimpos -d aimpos_spark -t -A \
  -c "UPDATE pipeline_runs SET status='CANCELLED', current_stage=NULL, updated_at=now() WHERE id='$RUN_ID' AND status NOT IN ('COMPLETED','FAILED','CANCELLED') RETURNING id||'|'||status;"
