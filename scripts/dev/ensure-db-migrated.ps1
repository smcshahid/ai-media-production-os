# Ensure PostgreSQL schema is at Alembic head before the dev worker starts (WP-3 / D-65).
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [int]$MaxWaitSec = 60
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

function Test-PostgresReady {
    docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql sh -c "pg_isready -U `$POSTGRES_USER -d `$POSTGRES_DB" 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Get-PsqlScalar {
    param([string]$Query)
    $user = "aimpos"
    $db = "aimpos_spark"
    foreach ($line in Get-Content .env) {
        if ($line -match '^\s*POSTGRES_USER=(.+)$') { $user = $Matches[1].Trim() }
        if ($line -match '^\s*POSTGRES_DB=(.+)$') { $db = $Matches[1].Trim() }
    }
    $raw = docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql `
        psql -U $user -d $db -t -A -c $Query
    return ($raw | Out-String).Trim()
}

Write-Host "=== Database migration check (Alembic head) ==="

if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env missing. Run: make env" -ForegroundColor Red
    exit 1
}

docker compose -f deploy/compose/docker-compose.yml --env-file .env up -d postgresql | Out-Null

$deadline = (Get-Date).AddSeconds($MaxWaitSec)
while ((Get-Date) -lt $deadline) {
    if (Test-PostgresReady) { break }
    Start-Sleep -Seconds 2
}

if (-not (Test-PostgresReady)) {
    Write-Host "ERROR: PostgreSQL not ready." -ForegroundColor Red
    exit 1
}

Write-Host "Applying Alembic migrations (upgrade head)..."
$repo = (Get-Location).Path
docker run --rm --network aimpos-spark_aimpos-spark --env-file .env `
    -v "${repo}:/repo" -w /repo/api python:3.12-slim `
    sh -c "pip install -q 'sqlalchemy>=2.0,<3.0' 'alembic>=1.13,<2.0' 'psycopg[binary]>=3.2,<4.0' -e /repo/packages/aimpos-core && alembic upgrade head"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Alembic migrate failed." -ForegroundColor Red
    exit 1
}

$version = Get-PsqlScalar "SELECT version_num FROM alembic_version;"
Write-Host "Database at Alembic revision: $version"

if ($version -lt "0006") {
    Write-Host "ERROR: Expected Alembic 0006 (character bible pilot)." -ForegroundColor Red
    exit 1
}

$indexCount = Get-PsqlScalar "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'asset_versions' AND indexname LIKE 'uq_%';"
if ([int]$indexCount -lt 2) {
    Write-Host "ERROR: Expected storyboard partial unique indexes." -ForegroundColor Red
    exit 1
}

Write-Host "Migration validation OK."
