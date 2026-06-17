# Phase 3B Olares cluster verification (in-cluster API)
param(
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
$verifySh = Join-Path $RepoRoot "deploy/k8s/phase3b-verify/verify_phase3b.sh"
$runSh = Join-Path $RepoRoot "deploy/k8s/phase3b-verify/run_olares_phase3b.sh"
foreach ($f in @($verifySh, $runSh)) {
    if (-not (Test-Path $f)) { throw "missing $f" }
}

Write-Host "Olares Phase 3B verify -> $OlaresHost"
scp -q $verifySh "${OlaresHost}:/tmp/verify_phase3b.sh"
scp -q $runSh "${OlaresHost}:/tmp/run_olares_phase3b.sh"
ssh -o BatchMode=yes -o ConnectTimeout=15 $OlaresHost "chmod +x /tmp/verify_phase3b.sh /tmp/run_olares_phase3b.sh && bash /tmp/run_olares_phase3b.sh"
