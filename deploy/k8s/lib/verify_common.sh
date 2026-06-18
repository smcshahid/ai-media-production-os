#!/usr/bin/env bash
# Shared Olares E2E verification helpers (Phase 8 / US-V05+).
# Source from acceptance scripts; do not execute directly.

verify_common_log() {
  echo "$(date -Iseconds) $*" >> "${EVID:?EVID}/e2e-olares.log"
  echo "$(date -Iseconds) $*" >&2
}

verify_common_psql() {
  ${K:?} exec -i aimpos-postgres-0 -n "${NS:?}" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"
}

verify_common_terminate_workflow() {
  local wf="$1"
  [ -n "$wf" ] || return 0
  verify_common_log "terminating temporal workflow $wf"
  $K exec deploy/temporal -n "$NS" -- tctl --address temporal:7233 workflow terminate \
    -w "$wf" -r "AIMPOS verification cleanup" >> "${EVID}/e2e-olares.log" 2>&1 || true
}

verify_common_wait_for_project_idle() {
  local max="${1:-120}" i count
  for i in $(seq 1 "$max"); do
    count=$(verify_common_psql -c "
      SELECT COUNT(*) FROM pipeline_runs
      WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
    " || echo 1)
    if [ "${count:-1}" = "0" ]; then
      verify_common_log "project idle (no active runs)"
      return 0
    fi
    verify_common_log "waiting for idle active_runs=$count (${i}/${max})"
    sleep 5
  done
  verify_common_log "WARN project still has active runs after ${max} polls"
  return 1
}

verify_common_cancel_active_runs() {
  local wf_ids
  verify_common_log "Cancelling non-terminal active runs for project"
  wf_ids=$(verify_common_psql -c "
    SELECT COALESCE(temporal_workflow_id, 'spark-pipeline-' || id::text)
    FROM pipeline_runs
    WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
  " || true)
  for wf in $wf_ids; do
    verify_common_terminate_workflow "$wf"
  done
  verify_common_psql -c "
    UPDATE pipeline_runs SET status='CANCELLED', current_stage=NULL, updated_at=NOW()
    WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
  " >> "${EVID}/e2e-olares.log" 2>&1 || true
  verify_common_wait_for_project_idle 120
}

verify_common_acquire_lock() {
  exec 9>"${EVID}/.e2e.lock"
  if ! flock -n 9; then
    verify_common_log "FAIL another E2E instance holds ${EVID}/.e2e.lock"
    exit 1
  fi
}

verify_common_poll_until() {
  local want_status="$1" want_stage="$2" want_scene="${3:-}" episode_id="${4:-}" max="${5:-1200}"
  local deadline=$(( $(date +%s) + max ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local url="${API:?}/pipeline/status?project_id=$PROJECT"
    if [ -n "$episode_id" ]; then url="${url}&episode_id=${episode_id}"; fi
    local body
    body=$(curl -sf -m 20 "$url" -H "${AUTH:?}" || echo '{}')
    local st stg scn
    st=$(echo "$body" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    stg=$(echo "$body" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    scn=$(echo "$body" | sed -n 's/.*"current_scene_index":\([0-9]*\).*/\1/p')
    verify_common_log "  poll status=$st stage=${stg:-null} scene=${scn:-null} ep=${episode_id:-legacy}"
    if [ "$st" = "FAILED" ]; then verify_common_log "FAIL pipeline FAILED: $body"; return 1; fi
    if [ "$st" = "$want_status" ]; then
      if [ -n "$want_stage" ] && [ "$stg" != "$want_stage" ]; then sleep 10; continue; fi
      if [ -n "$want_scene" ] && [ "$scn" != "$want_scene" ]; then sleep 10; continue; fi
      return 0
    fi
    sleep 15
  done
  verify_common_log "FAIL poll timeout want=$want_status/$want_stage scene=$want_scene"
  return 1
}

verify_common_approve() {
  local stage="$1" episode_id="${2:-}" attempt http
  local payload
  if [ -n "$episode_id" ]; then
    payload='{"project_id":"'"$PROJECT"'","episode_id":"'"$episode_id"'","stage":"'"$stage"'","decision":"APPROVED"}'
  else
    payload='{"project_id":"'"$PROJECT"'","stage":"'"$stage"'","decision":"APPROVED"}'
  fi
  for attempt in $(seq 1 12); do
    http=$(curl -s -m 60 -o /dev/null -w "%{http_code}" -X POST "${API}/pipeline/approve" \
      -H "$AUTH" -H 'Content-Type: application/json' -d "$payload" || echo 000)
    if [ "$http" = "200" ]; then
      echo >> "${EVID}/e2e-olares.log"
      return 0
    fi
    verify_common_log "approve retry $attempt http=$http stage=$stage"
    sleep 5
  done
  verify_common_log "FAIL approve stage=$stage after 12 attempts http=$http"
  return 1
}

verify_common_retry() {
  local attempts="$1" label="$2"
  shift 2
  local n rc=1
  for n in $(seq 1 "$attempts"); do
    verify_common_log "retry $label attempt $n/$attempts"
    if "$@"; then return 0; fi
    rc=$?
    verify_common_cancel_active_runs || true
    sleep 10
  done
  return "$rc"
}

verify_common_run_supplement() {
  local script="$1" label="$2"
  verify_common_log "========== SUPPLEMENT $label =========="
  if [ ! -f "$script" ]; then
    verify_common_log "FAIL supplement script missing: $script"
    return 1
  fi
  bash "$script"
}

verify_common_write_evidence() {
  local name="$1" content="$2"
  local path="${EVID}/${name}"
  printf '%s\n' "$content" > "$path"
  verify_common_log "evidence written $path"
}

verify_common_export_manifest_version() {
  local run_id="$1" expect="$2" zip="$3" manifest="$4"
  curl -sf -m 120 "${API}/export/${run_id}" -H "$AUTH" -o "$zip"
  unzip -p "$zip" manifest.json > "$manifest"
  local mv
  mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$manifest" | head -1)
  verify_common_log "export manifest_version=$mv expect=$expect size=$(wc -c < "$zip")"
  [ "$mv" = "$expect" ]
}

verify_common_source_helpers() {
  log() { verify_common_log "$@"; }
  psql() { verify_common_psql "$@"; }
  poll_until() { verify_common_poll_until "$@"; }
  approve() { verify_common_approve "$1" "${2:-}"; }
  cancel_active_runs() { verify_common_cancel_active_runs; }
  terminate_workflow() { verify_common_terminate_workflow "$@"; }
  wait_for_project_idle() { verify_common_wait_for_project_idle "$@"; }
}
