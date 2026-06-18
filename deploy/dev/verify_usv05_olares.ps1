# US-V05 Olares acceptance orchestrator (verification only)
param(
    [string]$OlaresHost = "olares@10.0.0.34",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$Date = Get-Date -Format "yyyy-MM-dd"
$EvidentRoot = Join-Path $RepoRoot "evidence/us-v05-verification/olares-$Date"
$LogDir = Join-Path $EvidentRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$scripts = @(
    "deploy/k8s/usv05-verify/olares_probe.sh",
    "deploy/k8s/usv05-verify/apply_0004_sql_olares.sh",
    "deploy/k8s/usv05-verify/verify_path_c_olares.sh"
)
foreach ($s in $scripts) {
    scp -q (Join-Path $RepoRoot $s) "${OlaresHost}:/tmp/$(Split-Path $s -Leaf)"
}

Write-Host "=== Olares probe (pre) ===" | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-pre.log")
ssh $OlaresHost "bash /tmp/olares_probe.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-pre.log") -Append

Write-Host "=== Apply migration 0004 ===" | Tee-Object -FilePath (Join-Path $LogDir "migration-0004.log")
ssh $OlaresHost "bash /tmp/apply_0004_sql_olares.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "migration-0004.log") -Append

Write-Host "=== Olares probe (post) ===" | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-post.log")
ssh $OlaresHost "bash /tmp/olares_probe.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-post.log") -Append

Write-Host "=== PATH C regression ===" | Tee-Object -FilePath (Join-Path $LogDir "path-c-olares.log")
$remote = @'
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv05-evidence-pathc
bash /tmp/verify_path_c_olares.sh
'@
ssh $OlaresHost $remote 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "path-c-olares.log") -Append
$pathCFail = $LASTEXITCODE

Write-Host "=== Fetch PATH C evidence ==="
scp -r -q "${OlaresHost}:/tmp/usv05-evidence-pathc/*" (Join-Path $EvidentRoot "path-c") 2>$null

Write-Host "PATH C exit=$pathCFail"
exit $pathCFail
