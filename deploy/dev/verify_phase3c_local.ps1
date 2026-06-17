# Phase 3C local verification
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [string]$ProjectId = ""
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if (-not (Test-Path .env)) { throw ".env missing" }
$tokenLine = Select-String -Path .env -Pattern '^AIMPOS_API_TOKEN=(.+)$' | Select-Object -First 1
if (-not $tokenLine) { throw "AIMPOS_API_TOKEN missing" }
$token = $tokenLine.Matches[0].Groups[1].Value.Trim()
$headers = @{ Authorization = "Bearer $token" }

$FAIL = 0
Write-Host "Phase 3C local verify start"

if (-not $ProjectId) {
    $ProjectId = (docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql psql -U aimpos -d aimpos_spark -t -A -c "SELECT id FROM projects ORDER BY created_at LIMIT 1;").Trim()
}
Write-Host "PROJECT_ID=$ProjectId"

function Invoke-CurlCheck {
    param([string]$Url, [hashtable]$Headers, [string]$OutFile, [int]$TimeoutSec = 30)
    $headerArgs = @()
    foreach ($key in $Headers.Keys) {
        $headerArgs += "-H"; $headerArgs += "$key`: $($Headers[$key])"
    }
    $args = @("-s", "-S", "--max-time", "$TimeoutSec", "-w", "`nHTTP=%{http_code}", "-o", $OutFile) + $headerArgs + @($Url)
    $meta = & curl.exe @args 2>&1
    $code = ($meta | Select-String -Pattern "HTTP=(\d+)" | ForEach-Object { $_.Matches[0].Groups[1].Value })
    return $code
}

$tmp = Join-Path $env:TEMP "aimpos-p3c-verify"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

Write-Host "========== P3C-01: audit pagination =========="
try {
    $jsonPath = Join-Path $tmp "audit-page.json"
    $code = Invoke-CurlCheck -Url "http://127.0.0.1:8000/audit?project_id=$ProjectId&limit=10&offset=0" -Headers $headers -OutFile $jsonPath
    if ($code -ne "200") { throw "bad status $code" }
    $body = Get-Content $jsonPath -Raw | ConvertFrom-Json
    if ($null -eq $body.total) { throw "missing total" }
    Write-Host "PASS total=$($body.total) events=$($body.events.Count) has_more=$($body.has_more)"
} catch {
    Write-Host "FAIL audit pagination: $($_.Exception.Message)"
    $FAIL = 1
}

Write-Host "========== P3C-02: audit export regression =========="
& "$RepoRoot/deploy/dev/verify_phase3b_local.ps1" -ProjectId $ProjectId
if ($LASTEXITCODE -ne 0) { $FAIL = 1 }

Write-Host "DONE FAIL=$FAIL"
exit $FAIL
