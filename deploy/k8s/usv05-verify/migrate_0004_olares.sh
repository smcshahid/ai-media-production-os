#!/usr/bin/env bash
# Apply Alembic 0004 on Olares postgres (acceptance migration step).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
REPO="${REPO_DIR:-/tmp/aimpos-usv05-src}"

PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
PGHOST=$($K get svc aimpos-postgres -n "$NS" -o jsonpath='{.spec.clusterIP}')
DATABASE_URL="postgresql+psycopg://aimpos:${PGPW}@${PGHOST}:5432/aimpos_spark"

if [ ! -d "$REPO/api/alembic" ]; then
  echo "ERROR: repo not found at $REPO — rsync source first"
  exit 1
fi

echo "Running alembic upgrade head against $PGHOST"
docker run --rm \
  -v "${REPO}:/repo" -w /repo/api \
  -e DATABASE_URL="$DATABASE_URL" \
  python:3.12-slim \
  sh -c "pip install -q 'sqlalchemy>=2.0,<3.0' 'alembic>=1.13,<2.0' 'psycopg[binary]>=3.2,<4.0' -e /repo/packages/aimpos-core && alembic upgrade head"

REV=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;")
echo "Alembic now at: $REV"
if [ "$REV" != "0004" ]; then
  echo "FAIL expected 0004"
  exit 1
fi
echo "PASS migration 0004"
