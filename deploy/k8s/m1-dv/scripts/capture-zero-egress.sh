#!/usr/bin/env bash
# M1-DV Phase D — document zero-egress observation during AIMPOS namespace operation.
# Adaptation of T-02-06 for raw K8s (no compose on Olares host).
set -euo pipefail

NS="${AIMPOS_NS:-aimpos-mwayolares}"
KUBECTL="${KUBECTL:-sudo k3s kubectl}"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "=== M1-DV zero-egress capture ==="
echo "timestamp_utc: $STAMP"
echo "namespace: $NS"
echo "method: kubectl exec network snapshot on aimpos-api pod (ESTABLISHED sockets)"
echo ""

if ! $KUBECTL get pod -n "$NS" -l app=aimpos-api -o name 2>/dev/null | grep -q .; then
  echo "status: DEFERRED — aimpos-api pod not running; re-run after deploy-api.sh"
  exit 0
fi

POD="$($KUBECTL get pod -n "$NS" -l app=aimpos-api -o jsonpath='{.items[0].metadata.name}')"
echo "pod: $POD"
echo ""
echo "--- ss -tn state established (api container) ---"
$KUBECTL exec -n "$NS" "$POD" -- sh -c 'command -v ss >/dev/null && ss -tn state established || netstat -tn 2>/dev/null || echo "no ss/netstat in image"' || true
echo ""
echo "--- DNS resolver (in-cluster only expected) ---"
$KUBECTL exec -n "$NS" "$POD" -- sh -c 'cat /etc/resolv.conf 2>/dev/null || true' || true
echo ""
echo "interpretation:"
echo "  PASS if established connections are cluster-internal (10.x, *.svc) during idle health only."
echo "  Image pull egress during install is out-of-band; note separately if observed."
echo "  Record lab firewall / Olares zero-egress policy compliance in M1-DV-PASS-REPORT.md."
