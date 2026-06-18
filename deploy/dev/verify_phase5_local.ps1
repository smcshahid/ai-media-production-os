# US-V06 Audio Narration Pilot — local verification
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$FAIL = 0
$LogDir = Join-Path $RepoRoot "evidence/us-v06-verification/local-$(Get-Date -Format yyyy-MM-dd)/logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "verify-local.log"

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $Message
    Add-Content -Path $LogFile -Value $line
}

Log "US-V06 Phase 5 local verify start"

Log "========== V06-01: Core narration tests =========="
Push-Location (Join-Path $RepoRoot "packages/aimpos-core")
python -m pytest tests/test_narration.py -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-core-narration.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL core narration pytest" } else { Log "PASS core narration pytest" }
Pop-Location

Log "========== V06-02: API unit tests =========="
Push-Location (Join-Path $RepoRoot "api")
python -m pytest tests/unit -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-api.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL api pytest" } else { Log "PASS api pytest" }
Pop-Location

Log "========== V06-03: Worker unit tests =========="
Push-Location (Join-Path $RepoRoot "worker")
python -m pytest tests/unit -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-worker.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL worker pytest" } else { Log "PASS worker pytest" }
Pop-Location

Log "========== V06-04: Web vitest =========="
Push-Location (Join-Path $RepoRoot "web")
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
npm test 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "vitest-web.txt")
$vitestExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($vitestExit -ne 0) { $FAIL = 1; Log "FAIL web vitest" } else { Log "PASS web vitest" }
Pop-Location

Log "DONE FAIL=$FAIL"
exit $FAIL
