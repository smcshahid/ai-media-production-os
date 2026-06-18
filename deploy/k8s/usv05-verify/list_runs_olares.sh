#!/usr/bin/env bash
PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
sudo k3s kubectl exec -i aimpos-postgres-0 -n aimpos-mwayolares -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark <<'SQL'
SELECT id::text, scene_count, status, created_at::date
FROM pipeline_runs
WHERE project_id='ba0c4636-817c-423b-9771-20100e080b76' AND status='COMPLETED'
ORDER BY created_at ASC;
SQL
