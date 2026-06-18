# US-V09 Full Platform Re-attestation — Local Verification (Phase 8)

param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$FAIL = 0
$LogDir = Join-Path $RepoRoot "evidence/us-v09-verification/local-$(Get-Date -Format yyyy-MM-dd)/logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "verify-local.log"

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $Message
    Add-Content -Path $LogFile -Value $line
}

Log "US-V09 Phase 8 platform re-attestation start"

Log "========== V09-01: Manifest validation =========="
python "$RepoRoot/scripts/release/validate-manifest.py" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "validate-manifest.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL manifest validation" } else { Log "PASS manifest validation" }

Log "========== V09-02: Export ladder unit tests (v1-v5) =========="
Push-Location (Join-Path $RepoRoot "api")
python -m pytest tests/unit/test_export.py tests/unit/test_multi_scene_export.py tests/unit/test_narration_export.py tests/unit/test_episode_export.py tests/unit/test_character_export.py tests/unit/test_character_snapshot_export.py -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-export-ladder.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL export ladder pytest" } else { Log "PASS export ladder pytest" }
Pop-Location

Log "========== V09-03: Episode-scoped approve (TD-P6.5-01) =========="
Push-Location (Join-Path $RepoRoot "api")
python -m pytest tests/unit/test_pipeline_approve.py -q 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pytest-approve-episode.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL approve episode pytest" } else { Log "PASS approve episode pytest" }
Pop-Location

Log "========== V09-04: Full platform verify-all =========="
& "$RepoRoot/deploy/dev/verify_all.ps1" -SkipManifest 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "verify-all.txt")
if ($LASTEXITCODE -ne 0) { $FAIL = 1; Log "FAIL verify-all" } else { Log "PASS verify-all" }

Log "DONE FAIL=$FAIL"
exit $FAIL
