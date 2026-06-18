# US-V08 Character Bible Pilot — Local Verification

param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$FAIL = 0
$LogDir = Join-Path $RepoRoot "evidence/us-v08-verification/local-$(Get-Date -Format yyyy-MM-dd)/logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "verify-local.log"

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $Message
    Add-Content -Path $LogFile -Value $line
}

Log "US-V08 Phase 7 local verify start"

Log "========== V08-01: Core character tests =========="
Push-Location (Join-Path $RepoRoot "packages/aimpos-core")
python -m pytest tests/test_character.py -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-core-character.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL core character pytest" } else { Log "PASS core character pytest" }
Pop-Location

Log "========== V08-02: API unit tests =========="
Push-Location (Join-Path $RepoRoot "api")
python -m pytest tests/unit -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-api.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL api pytest" } else { Log "PASS api pytest" }
Pop-Location

Log "========== V08-03: Worker unit tests =========="
Push-Location (Join-Path $RepoRoot "worker")
python -m pytest tests/unit -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-worker.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL worker pytest" } else { Log "PASS worker pytest" }
Pop-Location

Log "========== V08-04: Web vitest =========="
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
