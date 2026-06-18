# US-V09 supplemental export attestation for a COMPLETED Olares run.
param(
    [Parameter(Mandatory = $true)][string]$RunId,
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$EvidenceRoot = Join-Path $RepoRoot "evidence/us-v09-verification/olares-$(Get-Date -Format 'yyyy-MM-dd')"
$LogDir = Join-Path $EvidenceRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

scp -q (Join-Path $RepoRoot "deploy/k8s/usv09-verify/supplement_platform_path.sh") "${OlaresHost}:/tmp/"

$remote = @"
export TOKEN=`$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=`$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv09-evidence
chmod +x /tmp/supplement_platform_path.sh
bash /tmp/supplement_platform_path.sh $RunId
"@

$logFile = Join-Path $LogDir "supplement-platform-path.log"
ssh -o BatchMode=yes $OlaresHost $remote 2>&1 | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -ne 0) { exit 1 }

scp -q "${OlaresHost}:/tmp/usv09-evidence/platform-export.zip" (Join-Path $EvidenceRoot "platform-export.zip")
scp -q "${OlaresHost}:/tmp/usv09-evidence/platform-manifest.json" (Join-Path $EvidenceRoot "platform-manifest.json")
Write-Host "SUPPLEMENT PASS evidence=$EvidenceRoot"
exit 0
