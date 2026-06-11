#!/usr/bin/env bash
# Terminate a stale pipeline workflow and mark the run CANCELLED (verification cleanup).
set -euo pipefail
NS=aimpos-mwayolares
RUN_ID="${1:?usage: cancel_stale_run.sh RUN_ID}"
K="sudo k3s kubectl"
WF="spark-pipeline-${RUN_ID}"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

echo "Terminating workflow $WF"
$K exec deploy/temporal -n "$NS" -- tctl --address temporal:7233 workflow terminate \
  -w "$WF" -r "verification cleanup: stale run" 2>&1 || echo "(terminate skipped or already done)"

echo "Marking run $RUN_ID CANCELLED"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A \
  -c "UPDATE pipeline_runs SET status='CANCELLED', updated_at=now() WHERE id='$RUN_ID' AND status NOT IN ('COMPLETED','FAILED','CANCELLED') RETURNING id||'|'||status;"
