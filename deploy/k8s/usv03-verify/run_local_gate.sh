#!/usr/bin/env bash
# Local verification gate for US-V03 (pre-Olares).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DATE=$(date +%Y-%m-%d)
OUT="$ROOT/evidence/us-v03-verification/local-$DATE/logs"
mkdir -p "$OUT"

echo "========== API unit tests =========="
(cd "$ROOT/api" && python -m pytest -q 2>&1 | tee "$OUT/pytest-api.txt")
API_COUNT=$(grep -E '^[0-9]+ passed' "$OUT/pytest-api.txt" | tail -1 | awk '{print $1}')
echo "API_PASSED=$API_COUNT"

echo "========== Worker unit tests =========="
(cd "$ROOT/worker" && python -m pytest -q 2>&1 | tee "$OUT/pytest-worker.txt")

echo "========== Web unit tests =========="
(cd "$ROOT/web" && npm test -- --run 2>&1 | tee "$OUT/vitest-web.txt")
WEB_COUNT=$(grep -E 'Tests.*passed' "$OUT/vitest-web.txt" | tail -1 || true)
echo "WEB_RESULT=$WEB_COUNT"

echo "========== Web build =========="
(cd "$ROOT/web" && npm run build 2>&1 | tee "$OUT/web-build.txt")

echo "========== History route grep (EC-23-01) =========="
grep -r 'history' "$ROOT/web/dist/assets/"*.js 2>/dev/null | head -3 | tee "$OUT/history-route-grep.txt" || true
if grep -q '/history' "$ROOT/web/dist/assets/"*.js 2>/dev/null; then
  echo "HISTORY_ROUTE=PASS" | tee -a "$OUT/history-route-grep.txt"
else
  echo "HISTORY_ROUTE=FAIL" | tee -a "$OUT/history-route-grep.txt"
  exit 1
fi

echo "LOCAL_GATE=PASS logs=$OUT"
