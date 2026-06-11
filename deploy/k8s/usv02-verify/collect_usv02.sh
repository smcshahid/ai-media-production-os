#!/usr/bin/env bash
# Post-run SQL attestation → evidence/us-v02-verification/olares-<date>/sql/
set -euo pipefail
NS=aimpos-mwayolares
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
: "${RUN_ID:?set RUN_ID}"
K="sudo k3s kubectl"
OUT="${EVIDENCE_SQL_DIR:-/tmp/usv02-sql}"
mkdir -p "$OUT"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark "$@"; }

run_q() {
  local name="$1"
  shift
  echo "========== $name ==========" | tee "$OUT/$name.txt"
  psql -c "$*" | tee -a "$OUT/$name.txt"
}

run_q "v01-terminal" "SELECT id, status, current_stage, updated_at FROM pipeline_runs WHERE id='$RUN_ID';"
run_q "v02-approvals" "SELECT stage, decision, LEFT(rationale,80), created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
run_q "v03-asset-counts" "SELECT stage, COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' GROUP BY stage ORDER BY stage;"
run_q "v04-script-versions" "SELECT version, branch, content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version;"
run_q "v05-storyboard-batches" "SELECT version, COUNT(*) AS frame_count, array_agg(metadata_json->>'frame_index' ORDER BY (metadata_json->>'frame_index')::int) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' GROUP BY version ORDER BY version;"
run_q "v06-lineage" "SELECT p.stage, c.stage, COUNT(*) FROM lineage_edges le JOIN asset_versions p ON le.parent_id=p.id JOIN asset_versions c ON le.child_id=c.id WHERE p.project_id='$PROJECT' GROUP BY p.stage, c.stage ORDER BY 1,2;"
run_q "v07-agent-completions" "SELECT event_type, payload->>'agent', payload->>'stage', model_id, created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type IN ('AGENT_TASK_COMPLETED','STAGE_STARTED') ORDER BY created_at;"
run_q "v08-story-timing" "SELECT event_type, payload->>'stage', created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at LIMIT 40;"
run_q "v09-video-assets" "SELECT version, content_hash, metadata_json->>'logical_filename' filename, metadata_json->>'duration_sec' duration_sec, metadata_json->>'width' width, metadata_json->>'height' height, metadata_json->>'source' source FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO' ORDER BY version;"
run_q "v10-video-regen" "SELECT version, content_hash, created_at FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO' ORDER BY version;"
run_q "v11-lineage-video" "SELECT parent.stage, child.stage, COUNT(*) FROM lineage_edges le JOIN asset_versions parent ON le.parent_id=parent.id JOIN asset_versions child ON le.child_id=child.id WHERE parent.project_id='$PROJECT' AND child.stage='VIDEO' GROUP BY parent.stage, child.stage;"
run_q "v12-bundle-exported" "SELECT event_type, payload->>'manifest_hash' manifest_hash, payload->>'file_count' file_count, payload->>'zip_size_bytes' zip_size_bytes, payload->>'exported_at' exported_at, created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='BUNDLE_EXPORTED' ORDER BY created_at DESC LIMIT 3;"
run_q "v20-d51-storyboard-not-terminal" "SELECT stage, decision, created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' AND stage='STORYBOARD' AND decision='APPROVED';"
run_q "v47-d47-extension" "
SELECT version, metadata_json->>'frame_index' fi, content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=1 ORDER BY (metadata_json->>'frame_index')::int;
SELECT version, metadata_json->>'frame_index' fi, content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=2 ORDER BY (metadata_json->>'frame_index')::int;
SELECT decision, rationale FROM approvals WHERE pipeline_run_id='$RUN_ID' AND stage='STORYBOARD' AND decision='REJECTED';
SELECT payload, created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='REGENERATION_REQUESTED' AND payload->>'stage'='STORYBOARD';
"

echo "COLLECTED_SQL=$OUT"
