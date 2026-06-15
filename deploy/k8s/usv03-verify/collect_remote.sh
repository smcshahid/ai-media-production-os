#!/usr/bin/env bash
# Pull Olares US-V03 evidence to local evidence/us-v03-verification/olares-<date>/
set -euo pipefail
HOST="${OLARES_HOST:-olares@10.0.0.34}"
DATE="${EVIDENCE_DATE:-$(date +%Y-%m-%d)}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DEST="$ROOT/evidence/us-v03-verification/olares-$DATE"
mkdir -p "$DEST/logs" "$DEST/sql"

REMOTE_LOG=$(ssh "$HOST" 'ls -t /tmp/usv03-verify-*.log 2>/dev/null | head -1')
echo "REMOTE_LOG=$REMOTE_LOG"
scp "$HOST:${REMOTE_LOG}" "$DEST/logs/usv03-verify.log"
scp "$HOST:/tmp/usv03-usv02-e2e.log" "$DEST/logs/usv02-e2e.log" 2>/dev/null || true
scp "$HOST:/tmp/usv03-phase2-cross.log" "$DEST/logs/phase2-cross.log" 2>/dev/null || true
scp "$HOST:/tmp/usv03-path-b.log" "$DEST/logs/path-b.log" 2>/dev/null || true
scp "$HOST:/tmp/usv03-collect.log" "$DEST/logs/usv03-collect.log" 2>/dev/null || true
scp "$HOST:/tmp/usv03-us20-verify.log" "$DEST/logs/us20-verify.log" 2>/dev/null || true
scp "$HOST:/tmp/usv03-us22-verify.log" "$DEST/logs/us22-verify.log" 2>/dev/null || true
scp "$HOST:/tmp/usv03-us21-verify.log" "$DEST/logs/us21-verify.log" 2>/dev/null || true

SQL_DIR=$(ssh "$HOST" 'ls -td /tmp/usv03-sql-* 2>/dev/null | head -1')
if [ -n "$SQL_DIR" ]; then
  scp "$HOST:${SQL_DIR}/*.txt" "$DEST/sql/" 2>/dev/null || true
fi

echo "COLLECTED=$DEST"
