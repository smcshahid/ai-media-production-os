#Requires -Version 5.1
<#
.SYNOPSIS
  Build release-pinned container images from deploy/release/manifest.yaml.
#>
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [string]$ManifestPath = "",
    [switch]$SkipWorker
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if (-not $ManifestPath) {
    $ManifestPath = Join-Path $RepoRoot "deploy/release/manifest.yaml"
}
if (-not (Test-Path $ManifestPath)) { throw "manifest missing: $ManifestPath" }

$content = Get-Content $ManifestPath -Raw
function Get-ManifestValue {
    param([string]$Pattern)
    if ($content -match $Pattern) { return $Matches[1].Trim('"') }
    return $null
}

$version = Get-ManifestValue 'version:\s*"([^"]+)"'
$apiTag = Get-ManifestValue 'aimpos-api[\s\S]*?tag:\s*"([^"]+)"'
$webTag = Get-ManifestValue 'aimpos-web[\s\S]*?tag:\s*"([^"]+)"'
$workerTag = Get-ManifestValue 'aimpos-worker[\s\S]*?tag:\s*"([^"]+)"'

if (-not $version) { throw "could not parse release.version from manifest" }

$apiImage = "aimpos-api:$apiTag"
$webImage = "aimpos-web:$webTag"
$workerImage = "aimpos-worker:$workerTag"

Write-Host "Building release images for $version"
Write-Host "  API:    $apiImage"
Write-Host "  Web:    $webImage"
Write-Host "  Worker: $workerImage"

docker build -f api/Dockerfile -t $apiImage .
if ($LASTEXITCODE -ne 0) { throw "api build failed" }

docker build -f web/Dockerfile --build-arg VITE_API_URL= -t $webImage .
if ($LASTEXITCODE -ne 0) { throw "web build failed" }

if (-not $SkipWorker) {
    docker build -f worker/Dockerfile -t $workerImage .
    if ($LASTEXITCODE -ne 0) { throw "worker build failed" }
}

$outDir = Join-Path $env:TEMP "aimpos-release-$version"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$apiTar = Join-Path $outDir "aimpos-api-$apiTag.tar"
$webTar = Join-Path $outDir "aimpos-web-$webTag.tar"
docker save $apiImage -o $apiTar
docker save $webImage -o $webTar
Write-Host "Saved $apiTar"
Write-Host "Saved $webTar"

if (-not $SkipWorker) {
    $workerTar = Join-Path $outDir "aimpos-worker-$workerTag.tar"
    docker save $workerImage -o $workerTar
    Write-Host "Saved $workerTar"
}

Write-Host "Release build complete. Output: $outDir"
Write-Host "Deploy with deploy/k8s/phase3d-verify/deploy_release.sh on Olares host."
