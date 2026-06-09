# GitHub cleanup — run from repo root after setting your token
#
# Option A — environment variable:
#   $env:GITHUB_TOKEN = "ghp_your_token_here"
#   python backlog/cleanup_github.py --dry-run
#   python backlog/cleanup_github.py
#
# Option B — gitignored file (one line, no quotes):
#   Set-Content -Path backlog/.github-token -Value "ghp_your_token_here" -NoNewline
#   python backlog/cleanup_github.py

Write-Host "AIMPOS GitHub cleanup" -ForegroundColor Cyan
Write-Host "Requires GITHUB_TOKEN or backlog/.github-token" -ForegroundColor Yellow

if (-not $env:GITHUB_TOKEN -and -not (Test-Path "backlog/.github-token")) {
    Write-Host ""
    Write-Host "Set token first:" -ForegroundColor Red
    Write-Host '  $env:GITHUB_TOKEN = "ghp_your_token"'
    exit 1
}

python backlog/cleanup_github.py --dry-run
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
$confirm = Read-Host "Apply changes? (y/N)"
if ($confirm -eq "y") {
    python backlog/cleanup_github.py
}
