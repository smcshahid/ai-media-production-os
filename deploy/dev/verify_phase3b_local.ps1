# Phase 3B local verification — audit export, run history, asset UX
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
Write-Host "Phase 3B local verify start"

if (-not $ProjectId) {
    $ProjectId = (docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql psql -U aimpos -d aimpos_spark -t -A -c "SELECT id FROM projects ORDER BY created_at LIMIT 1;").Trim()
}
Write-Host "PROJECT_ID=$ProjectId"

function Invoke-CurlCheck {
    param(
        [string]$Url,
        [hashtable]$Headers,
        [string]$OutFile,
        [int]$TimeoutSec = 30
    )
    $headerArgs = @()
    foreach ($key in $Headers.Keys) {
        $headerArgs += "-H"
        $headerArgs += "$key`: $($Headers[$key])"
    }
    $args = @(
        "-s", "-S", "--max-time", "$TimeoutSec",
        "-w", "`nHTTP=%{http_code} SIZE=%{size_download}",
        "-o", $OutFile
    ) + $headerArgs + @($Url)
    $meta = & curl.exe @args 2>&1
    $code = ($meta | Select-String -Pattern "HTTP=(\d+)" | ForEach-Object { $_.Matches[0].Groups[1].Value })
    $size = ($meta | Select-String -Pattern "SIZE=(\d+)" | ForEach-Object { $_.Matches[0].Groups[1].Value })
    return @{ Code = $code; Size = $size; Meta = ($meta -join "`n") }
}

$tmp = Join-Path $env:TEMP "aimpos-p3b-verify"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

Write-Host "========== P3B-01: audit export JSON =========="
try {
    $jsonPath = Join-Path $tmp "audit.json"
    $json = Invoke-CurlCheck -Url "http://127.0.0.1:8000/audit/export?project_id=$ProjectId&format=json" -Headers $headers -OutFile $jsonPath
    if ($json.Code -ne "200") { throw "bad status $($json.Code)" }
    Write-Host "PASS json bytes=$($json.Size)"
} catch {
    Write-Host "FAIL audit export json: $($_.Exception.Message)"
    $FAIL = 1
}

Write-Host "========== P3B-02: audit export CSV =========="
try {
    $csvPath = Join-Path $tmp "audit.csv"
    $csv = Invoke-CurlCheck -Url "http://127.0.0.1:8000/audit/export?project_id=$ProjectId&format=csv" -Headers $headers -OutFile $csvPath
    if ($csv.Code -ne "200") { throw "bad status $($csv.Code)" }
    $csvHead = Get-Content -Path $csvPath -TotalCount 1
    if ($csvHead -notmatch "event_type") { throw "missing header" }
    Write-Host "PASS csv bytes=$($csv.Size)"
} catch {
    Write-Host "FAIL audit export csv: $($_.Exception.Message)"
    $FAIL = 1
}

Write-Host "========== P3B-03: pipeline run list =========="
try {
    $runs = Invoke-RestMethod -Uri "http://127.0.0.1:8000/pipeline/runs?project_id=$ProjectId" -Headers $headers -TimeoutSec 15
    Write-Host "PASS runs=$($runs.runs.Count)"
} catch {
    Write-Host "FAIL pipeline runs"
    $FAIL = 1
}

Write-Host "========== P3B-04: audit API regression =========="
try {
    $audit = Invoke-RestMethod -Uri "http://127.0.0.1:8000/audit?project_id=$ProjectId" -Headers $headers -TimeoutSec 15
    Write-Host "PASS audit events=$($audit.events.Count)"
} catch {
    Write-Host "FAIL audit API"
    $FAIL = 1
}

Write-Host "========== P3B-05: asset history regression =========="
try {
    $hist = Invoke-RestMethod -Uri "http://127.0.0.1:8000/assets/history?project_id=$ProjectId" -Headers $headers -TimeoutSec 15
    Write-Host "PASS history stages=$($hist.stages.Count)"
} catch {
    Write-Host "FAIL asset history"
    $FAIL = 1
}

Write-Host "DONE FAIL=$FAIL"
exit $FAIL
