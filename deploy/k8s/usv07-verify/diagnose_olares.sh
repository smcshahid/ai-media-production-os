#!/usr/bin/env bash
# US-V07 Olares diagnostic — E2E, pipeline, GPU, worker.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PROJECT=ba0c4636-817c-423b-9771-20100e080b76

echo "=== E2E process ==="
pgrep -af verify_usv07 || echo "no verify_usv07_e2e.sh running"

echo "=== E2E log tail (e2e-olares.log) ==="
tail -25 /tmp/usv07-evidence/e2e-olares.log 2>/dev/null || echo "no e2e-olares.log"

echo "=== E2E nohup tail ==="
tail -10 /tmp/usv07-e2e-nohup.log 2>/dev/null || echo "no nohup log"

echo "=== PASS/FAIL summary ==="
grep -E 'PASS PATH|FAIL PATH|DONE FAIL' /tmp/usv07-evidence/e2e-olares.log 2>/dev/null | tail -20

echo "=== summary.txt ==="
cat /tmp/usv07-evidence/summary.txt 2>/dev/null || echo "no summary.txt"

echo "=== Pods (aimpos + comfy + ollama) ==="
$K get pods -n "$NS" -o wide 2>/dev/null | grep -E 'NAME|aimpos|comfy|ollama|gpu' || $K get pods -n "$NS" -o wide

echo "=== Deployments images ==="
$K get deploy -n "$NS" -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image,READY:.status.readyReplicas 2>/dev/null | head -20

echo "=== Active pipeline runs (DB) ==="
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<SQL
SELECT id::text, status, current_stage, current_scene_index, scene_count, episode_id::text, updated_at
FROM pipeline_runs
WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL')
ORDER BY updated_at DESC LIMIT 5;
SQL

echo "=== Recent runs (last 5) ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<SQL
SELECT id::text, status, current_stage, scene_count, episode_id IS NOT NULL as ep, updated_at
FROM pipeline_runs WHERE project_id='$PROJECT'
ORDER BY updated_at DESC LIMIT 5;
SQL

echo "=== API pipeline status ==="
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
curl -sf -m 10 "http://${API}:8000/pipeline/status?project_id=$PROJECT" -H "Authorization: Bearer ${TOKEN}" 2>/dev/null || echo "API status failed"
echo

echo "=== Worker logs (last 40 lines) ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=40 2>/dev/null || echo "worker logs unavailable"

echo "=== Temporal worker activity (grep) ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=200 2>/dev/null | grep -iE 'error|fail|comfy|ollama|gpu|video|storyboard' | tail -20 || true

echo "=== GPU / nvidia (host) ==="
if command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv 2>/dev/null; else echo "nvidia-smi not in PATH"; fi

echo "=== ComfyUI related pods all namespaces ==="
$K get pods -A 2>/dev/null | grep -iE 'comfy|ollama|gpu' || echo "no comfy/ollama pods in cluster grep"
