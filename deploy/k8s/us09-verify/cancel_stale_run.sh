#!/usr/bin/env bash
# Mark the stale pre-fix pipeline run CANCELLED (Temporal workflow already terminated).
# Verification-environment cleanup only — uses existing PipelineRunStatus.CANCELLED.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
RUN_ID=8c35926c-0a4e-44ed-ac5a-ea3c178902cd
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A \
  -c "UPDATE pipeline_runs SET status='CANCELLED', updated_at=now() WHERE id='$RUN_ID' AND status NOT IN ('COMPLETED','FAILED','CANCELLED') RETURNING id||'|'||status;"
