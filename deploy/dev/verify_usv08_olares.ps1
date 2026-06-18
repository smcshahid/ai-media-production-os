# US-V08 Olares acceptance orchestrator (verification + deploy)
param(
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [switch]$SkipBuild,
    [switch]$SkipE2E
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$Date = Get-Date -Format "yyyy-MM-dd"
$EvidenceRoot = Join-Path $RepoRoot "evidence/us-v08-verification/olares-$Date"
$LogDir = Join-Path $EvidenceRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $Message
    Add-Content -Path (Join-Path $LogDir "orchestrator.log") -Value $line
}

$scripts = @(
    "deploy/k8s/usv08-verify/olares_probe.sh",
    "deploy/k8s/usv08-verify/apply_0006_sql_olares.sh",
    "deploy/k8s/usv08-verify/build_usv08_olares.sh",
    "deploy/k8s/usv08-verify/deploy_usv08.sh",
    "deploy/k8s/usv08-verify/verify_usv08_e2e.sh"
)
foreach ($s in $scripts) {
    scp -q (Join-Path $RepoRoot $s) "${OlaresHost}:/tmp/$(Split-Path $s -Leaf)"
}

Log "=== Sync source to Olares ==="
$tarPath = Join-Path $env:TEMP "aimpos-usv08-src.tgz"
if (Test-Path $tarPath) { Remove-Item $tarPath -Force }
tar --exclude=node_modules --exclude=.git --exclude=evidence --exclude=__pycache__ -czf $tarPath -C $RepoRoot .
scp -q $tarPath "${OlaresHost}:/tmp/aimpos-usv08-src.tgz"
ssh -o BatchMode=yes $OlaresHost "rm -rf /tmp/aimpos-usv08-src && mkdir -p /tmp/aimpos-usv08-src && tar -xzf /tmp/aimpos-usv08-src.tgz -C /tmp/aimpos-usv08-src"
Log "Source synced to /tmp/aimpos-usv08-src"

Log "=== Olares probe (pre) ==="
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
ssh -o BatchMode=yes $OlaresHost "bash /tmp/olares_probe.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-pre.log")

Log "=== Apply migration 0006 ==="
ssh -o BatchMode=yes $OlaresHost "bash /tmp/apply_0006_sql_olares.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "migration-0006.log")

if (-not $SkipBuild) {
    $Tag = "usv08-phase7"
    $TarDir = Join-Path $env:TEMP "aimpos-usv08-tars"
    New-Item -ItemType Directory -Force -Path $TarDir | Out-Null
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    Log "=== Build usv08-phase7 images locally (Olares has nerdctl only) ==="
    docker build -f api/Dockerfile -t "aimpos-api:${Tag}" . 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "build-api.log")
    if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEap; Log "FAIL build api"; exit 1 }
    docker build -f worker/Dockerfile -t "aimpos-worker:${Tag}" . 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "build-worker.log")
    if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEap; Log "FAIL build worker"; exit 1 }
    docker build -f web/Dockerfile --build-arg VITE_API_URL= -t "aimpos-web:${Tag}" . 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "build-web.log")
    if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEap; Log "FAIL build web"; exit 1 }

    $apiTar = Join-Path $TarDir "aimpos-api-${Tag}.tar"
    $workerTar = Join-Path $TarDir "aimpos-worker-${Tag}.tar"
    $webTar = Join-Path $TarDir "aimpos-web-${Tag}.tar"
    docker save "aimpos-api:${Tag}" -o $apiTar 2>&1 | Out-Null
    docker save "aimpos-worker:${Tag}" -o $workerTar 2>&1 | Out-Null
    docker save "aimpos-web:${Tag}" -o $webTar 2>&1 | Out-Null
    $ErrorActionPreference = $prevEap

    Log "=== Upload image tars to Olares ==="
    scp -q $apiTar $workerTar $webTar "${OlaresHost}:/tmp/"
    if ($LASTEXITCODE -ne 0) { Log "FAIL scp tars"; exit 1 }

    Log "=== Deploy usv08-phase7 ==="
    $ErrorActionPreference = "Continue"
    ssh -o BatchMode=yes $OlaresHost "chmod +x /tmp/deploy_usv08.sh /tmp/verify_usv08_e2e.sh && bash /tmp/deploy_usv08.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "deploy-usv08.log")
    $deployExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    if ($deployExit -ne 0) { Log "FAIL deploy"; exit 1 }
}

Log "=== Olares probe (post) ==="
ssh -o BatchMode=yes $OlaresHost "bash /tmp/olares_probe.sh" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "olares-probe-post.log")
$ErrorActionPreference = $prevEap

if ($SkipE2E) {
    Log "E2E skipped by flag"
    exit 0
}

Log "=== US-V08 E2E (Paths A-E) - long running ==="
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$remote = @'
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv08-evidence
bash /tmp/verify_usv08_e2e.sh
'@
ssh -o BatchMode=yes $OlaresHost $remote 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "e2e-olares.log")
$e2eFail = $LASTEXITCODE
$ErrorActionPreference = $prevEap

Log "=== Fetch evidence ==="
foreach ($subdir in @("path-a","path-b","path-c1","path-c2","path-d","path-e")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceRoot $subdir) | Out-Null
}
scp -r -q "${OlaresHost}:/tmp/usv08-evidence/*" $EvidenceRoot 2>$null

# Organize path artifacts into subdirs when present at root
$pathMap = @{
    "path-A" = "path-a"
    "path-B" = "path-b"
    "path-C1" = "path-c1"
    "path-C2" = "path-c2"
    "path-D" = "path-d"
    "path-E" = "path-e"
}
foreach ($prefix in $pathMap.Keys) {
    Get-ChildItem -Path $EvidenceRoot -Filter "${prefix}*" -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Force $_.FullName (Join-Path $EvidenceRoot $pathMap[$prefix])
    }
}

Log "E2E exit=$e2eFail"
exit $e2eFail
