#!/usr/bin/env bash
# Shared Olares deployment helpers (Phase 8 — TD-P75-01).
# Source from deploy_usv*.sh scripts; do not execute directly.

olares_deploy_rollout() {
  local deployment="$1" container="$2" image="$3"
  echo "Rolling $deployment -> $image"
  if ! $K set image "deployment/${deployment}" "${container}=${image}" -n "$NS" 2>/dev/null; then
    $K set image "deployment/${deployment}" "${deployment}=${image}" -n "$NS"
  fi
  $K rollout status "deployment/${deployment}" -n "$NS" --timeout=300s
  olares_deploy_recycle_pods "$deployment"
  $K rollout status "deployment/${deployment}" -n "$NS" --timeout=300s
}

olares_deploy_recycle_pods() {
  local deployment="$1"
  echo "Recycling pods for $deployment (Olares set-image may not refresh running containers)"
  $K delete pod -l "app=${deployment}" -n "$NS" --wait=true
}

olares_deploy_import_tar() {
  local tar="$1" image="$2"
  echo "Importing $tar -> $image"
  $CTR images import "$tar"
}

olares_deploy_from_manifest() {
  local manifest="${1:-/tmp/aimpos-manifest.yaml}"
  if [ -f "$manifest" ]; then
    # shellcheck source=/dev/null
    source "${OLARES_MANIFEST_LOADER:-/tmp/load-manifest-env.sh}" "$manifest" /tmp
  fi
}
