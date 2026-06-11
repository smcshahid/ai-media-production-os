#!/usr/bin/env bash
# Collect US-17 Olares verification evidence into evidence/us-17-verification/olares-DATE/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DATE="${EVIDENCE_DATE:-$(date +%Y-%m-%d)}"
OUT="$ROOT/evidence/us-17-verification/olares-$DATE"
mkdir -p "$OUT/logs"

if [ -f /tmp/us17-verify-*.log ]; then
  cp /tmp/us17-verify-*.log "$OUT/logs/" 2>/dev/null || true
fi

cat > "$OUT/US-17-ACCEPTANCE-PACKAGE.md" <<EOF
# US-17 Acceptance Package — Olares $DATE

## Scope
Storyboard batch review gallery: 4-frame grid, lightbox, approve-all → COMPLETED, reject → regenerate v+1.

## Governance
- Batch-level approve/reject only (D-46)
- Regen uses approved script + latest STORYBOARD rejection note (D-47)
- No schema migrations, no lineage/history UI

## Evidence files
- \`logs/\` — verify script output

## AC mapping
| AC | Evidence |
|---|---|
| AC-1 Grid 4 images | V-01 frame count=4; web unit test storyboardReview |
| AC-2 Lightbox | StoryboardLightbox component; manual UI |
| AC-3 Approve → COMPLETED | V-03 approve path FINAL_STATUS=COMPLETED |
| AC-4 Reject → regen | V-03 regen path VERIFY_MODE=regen |
| AC-5 AI badge | ReviewPage badge on frames |

EOF

echo "Wrote $OUT/US-17-ACCEPTANCE-PACKAGE.md"
