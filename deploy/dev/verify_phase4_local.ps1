# US-V05 Multi-Scene Pilot - local verification
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$FAIL = 0
$LogDir = Join-Path $RepoRoot "evidence/us-v05-verification/local-$(Get-Date -Format yyyy-MM-dd)/logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "verify-local.log"

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $Message
    Add-Content -Path $LogFile -Value $line
}

Log "US-V05 Phase 4 local verify start"

Log "========== V05-01: API unit tests =========="
Push-Location (Join-Path $RepoRoot "api")
python -m pytest tests/unit -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-api.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL api pytest" } else { Log "PASS api pytest" }
Pop-Location

Log "========== V05-02: Worker unit tests =========="
Push-Location (Join-Path $RepoRoot "worker")
python -m pytest tests/unit -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-worker.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL worker pytest" } else { Log "PASS worker pytest" }
Pop-Location

Log "========== V05-03: Web vitest =========="
Push-Location (Join-Path $RepoRoot "web")
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
npm run test -- --run 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "vitest-web.txt")
$vitestExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($vitestExit -ne 0) { $FAIL = 1; Log "FAIL web vitest" } else { Log "PASS web vitest" }
Pop-Location

Log "========== V05-04: Alembic contract (manifest-driven) =========="
if (Test-Path .env) {
    try {
        & "$RepoRoot/scripts/dev/ensure-db-migrated.ps1"
        if ($LASTEXITCODE -ne 0) { throw "migration gate failed" }
        Log "PASS migration gate"
    } catch {
        Log "WARN migration check skipped or failed: $($_.Exception.Message)"
    }
} else {
    Log "WARN .env missing - skip live migration check"
}

Log "========== V05-05: Pipeline start scene_count API (if stack up) =========="
if (Test-Path .env) {
    try {
        $tokenLine = Select-String -Path .env -Pattern '^AIMPOS_API_TOKEN=(.+)$' | Select-Object -First 1
        if ($null -eq $tokenLine) {
            Log "WARN AIMPOS_API_TOKEN missing - skip live pipeline probe"
        } else {
            $token = $tokenLine.Matches[0].Groups[1].Value.Trim()
            $statusCode = (curl.exe -s -o NUL -w "%{http_code}" -H "Authorization: Bearer $token" "http://127.0.0.1:8000/health" 2>$null)
            if ($statusCode -eq "200") {
                $body = '{"project_id":"00000000-0000-0000-0000-000000000001","scene_count":2}'
                $resp = curl.exe -s -w "`nHTTP=%{http_code}" -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d $body "http://127.0.0.1:8000/pipeline/start" 2>&1
                Log "INFO pipeline/start probe: $resp"
            } else {
                Log "WARN API not reachable - skip live pipeline probe"
            }
        }
    } catch {
        Log "WARN live API probe failed: $($_.Exception.Message)"
    }
}

Log "DONE FAIL=$FAIL"
exit $FAIL
