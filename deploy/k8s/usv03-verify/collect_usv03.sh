#!/usr/bin/env bash
# Post-run SQL attestation for US-V03 → evidence directory.
set -euo pipefail
NS=aimpos-mwayolares
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
: "${RUN_ID:?set RUN_ID}"
K="sudo k3s kubectl"
OUT="${EVIDENCE_SQL_DIR:-/tmp/usv03-sql}"
mkdir -p "$OUT"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark "$@"; }

run_q() {
  local name="$1"
  shift
  echo "========== $name ==========" | tee "$OUT/$name.txt"
  psql -c "$*" | tee -a "$OUT/$name.txt"
}

run_q "v03-terminal" "SELECT id, status, current_stage, updated_at FROM pipeline_runs WHERE id='$RUN_ID';"
run_q "v03-approvals" "SELECT stage, decision, LEFT(rationale,80), created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
run_q "v03-asset-counts" "SELECT stage, COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' GROUP BY stage ORDER BY stage;"
run_q "v03-lineage-edges" "SELECT p.stage, c.stage, COUNT(*) FROM lineage_edges le JOIN asset_versions p ON le.parent_id=p.id JOIN asset_versions c ON le.child_id=c.id WHERE p.project_id='$PROJECT' GROUP BY p.stage, c.stage ORDER BY 1,2;"
run_q "v03-history-rows" "SELECT stage, COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' GROUP BY stage ORDER BY stage;"
run_q "v03-no-writes" "SELECT COUNT(*) AS asset_versions_total FROM asset_versions;"
run_q "v03-bundle-exported" "SELECT event_type, payload->>'manifest_hash', payload->>'file_count', payload->>'zip_size_bytes' FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='BUNDLE_EXPORTED' ORDER BY created_at DESC LIMIT 1;"
run_q "v03-lineage-api-parity" "
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE p.project_id='$PROJECT' AND c.project_id='$PROJECT'
  AND (p.pipeline_run_id='$RUN_ID' OR c.pipeline_run_id='$RUN_ID');
"

echo "COLLECTED_SQL=$OUT"
