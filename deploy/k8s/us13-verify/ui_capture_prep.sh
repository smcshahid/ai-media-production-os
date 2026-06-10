#!/usr/bin/env bash
# Start fresh pipeline for UI screenshot capture (V1 + V4).
set -euo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?}"
: "${PROJECT:?}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-13 UI Capture","paragraph":"A gardener on Mars must decide whether to share a miraculous biome with the colony council before they arrive to claim the discovery for corporate interests.","style_note":"cinematic"}'
echo
START=$(curl -s -m 30 -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
DEADLINE=$(( $(date +%s) + 900 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORY" ]; then echo "READY=$S"; exit 0; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 10
done
exit 1
