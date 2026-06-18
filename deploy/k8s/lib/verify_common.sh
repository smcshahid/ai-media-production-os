#!/usr/bin/env bash
# Shared Olares E2E verification helpers (Phase 6.5 / US-V08+).
# Source from acceptance scripts; do not execute directly.
verify_common_log() {
  echo "$(date -Iseconds) $*" >> "${EVID:?EVID_DIR}/e2e-olares.log"
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
  exec 9>"$EVID/.e2e.lock"
  if ! flock -n 9; then
    verify_common_log "FAIL another E2E instance holds $EVID/.e2e.lock"
    exit 1
  fi
}
