# US-V07 Olares acceptance orchestrator (verification + deploy)
param(
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [switch]$SkipBuild,
    [switch]$SkipE2E
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$Date = Get-Date -Format "yyyy-MM-dd"
$EvidenceRoot = Join-Path $RepoRoot "evidence/us-v07-verification/olares-$Date"
$LogDir = Join-Path $EvidenceRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $Message
    Add-Content -Path (Join-Path $LogDir "orchestrator.log") -Value $line
}

$scripts = @(
    "deploy/k8s/usv07-verify/olares_probe.sh",
    "deploy/k8s/usv07-verify/apply_0005_sql_olares.sh",
    "deploy/k8s/usv07-verify/build_usv07_olares.sh",
    "deploy/k8s/usv07-verify/deploy_usv07.sh",
    "deploy/k8s/usv07-verify/verify_usv07_e2e.sh"
)
foreach ($s in $scripts) {
    scp -q (Join-Path $RepoRoot $s) "${OlaresHost}:/tmp/$(Split-Path $s -Leaf)"
}

Log "=== Sync source to Olares ==="
$tarPath = Join-Path $env:TEMP "aimpos-usv07-src.tgz"
if (Test-Path $tarPath) { Remove-Item $tarPath -Force }
tar --exclude=node_modules --exclude=.git --exclude=evidence --exclude=__pycache__ -czf $tarPath -C $RepoRoot .
scp -q $tarPath "${OlaresHost}:/tmp/aimpos-usv07-src.tgz"
ssh -o BatchMode=yes $OlaresHost "rm -rf /tmp/aimpos-usv07-src && mkdir -p /tmp/aimpos-usv07-src && tar -xzf /tmp/aimpos-usv07-src.tgz -C /tmp/aimpos-usv07-src"
Log "Source synced to /tmp/aimpos-usv07-src"

Log "=== Olares probe (pre) ==="
ssh -o BatchMode=yes $OlaresHost "bash /tmp/olares_probe.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-pre.log")

Log "=== Apply migration 0005 ==="
ssh -o BatchMode=yes $OlaresHost "bash /tmp/apply_0005_sql_olares.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "migration-0005.log")

if (-not $SkipBuild) {
    Log "=== Build usv07-phase6 images (may take several minutes) ==="
    ssh -o BatchMode=yes $OlaresHost "chmod +x /tmp/build_usv07_olares.sh /tmp/deploy_usv07.sh /tmp/verify_usv07_e2e.sh && REPO_DIR=/tmp/aimpos-usv07-src bash /tmp/build_usv07_olares.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "build-usv07.log")
    if ($LASTEXITCODE -ne 0) { Log "FAIL build"; exit 1 }

    Log "=== Deploy usv07-phase6 ==="
    ssh -o BatchMode=yes $OlaresHost "bash /tmp/deploy_usv07.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "deploy-usv07.log")
    if ($LASTEXITCODE -ne 0) { Log "FAIL deploy"; exit 1 }
}

Log "=== Olares probe (post) ==="
ssh -o BatchMode=yes $OlaresHost "bash /tmp/olares_probe.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-post.log")

if ($SkipE2E) {
    Log "E2E skipped by flag"
    exit 0
}

Log "=== US-V07 E2E (Paths A-E) - long running ==="
$remote = @'
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv07-evidence
bash /tmp/verify_usv07_e2e.sh
'@
ssh -o BatchMode=yes $OlaresHost $remote 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "e2e-olares.log")
$e2eFail = $LASTEXITCODE

Log "=== Fetch evidence ==="
foreach ($subdir in @("path-a","path-b","path-c1","path-c2","path-d","path-e")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceRoot $subdir) | Out-Null
}
scp -r -q "${OlaresHost}:/tmp/usv07-evidence/*" $EvidenceRoot 2>$null

Log "E2E exit=$e2eFail"
exit $e2eFail
