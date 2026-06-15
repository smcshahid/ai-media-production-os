#!/usr/bin/env bash
# Copy US-V03 verify bundle + dependencies to Olares and run Path A.
set -euo pipefail
HOST="${OLARES_HOST:-olares@10.0.0.34}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

echo "Copying US-V03 verify scripts to $HOST:/tmp/"
scp "$ROOT/deploy/k8s/usv03-verify/"*.sh "$ROOT/deploy/k8s/usv03-verify/cross_feature.py" "$HOST:/tmp/"
scp "$ROOT/deploy/k8s/usv02-verify/create_project.sh" "$ROOT/deploy/k8s/usv02-verify/prep_comfyui.sh" "$HOST:/tmp/"
scp "$ROOT/deploy/k8s/us20-verify/verify_us20.sh" "$HOST:/tmp/"
scp "$ROOT/deploy/k8s/us22-verify/verify_us22.sh" "$HOST:/tmp/"
scp "$ROOT/deploy/k8s/us21-verify/"{verify_us21.sh,ws_smoke.py} "$HOST:/tmp/"

echo "Starting remote verification (60-90+ min)..."
ssh "$HOST" 'bash /tmp/run_remote.sh'
