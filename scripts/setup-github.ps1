# One-time GitHub setup for AIMPOS-Spark Visual (Cursor + gh + MCP).
# Run from repo root:  .\scripts\setup-github.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== AIMPOS GitHub setup ===" -ForegroundColor Cyan

# 1. Verify gh CLI auth
Write-Host ""
Write-Host "[1/5] Checking gh auth..."
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: gh auth login -h github.com -p ssh -w" -ForegroundColor Yellow
    exit 1
}

# 2. Optional: project board scope (non-fatal, skip if non-interactive)
Write-Host ""
Write-Host "[2/5] GitHub Projects scope (optional)..."
Write-Host "  Run manually if you use a Project board: gh auth refresh -h github.com -s read:project"

# 3. Store token in user env for Cursor GitHub MCP (never print the token)
Write-Host ""
Write-Host "[3/5] Syncing GITHUB_PAT to Windows user environment (for Cursor MCP)..."
$token = (gh auth token).Trim()
if (-not $token) {
    Write-Host "  FAIL - gh auth token returned empty." -ForegroundColor Red
    exit 1
}
[System.Environment]::SetEnvironmentVariable("GITHUB_PAT", $token, "User")
$env:GITHUB_PAT = $token
Write-Host "  OK - GITHUB_PAT set (user scope). Restart Cursor to pick it up for MCP."

# 4. Verify repo access via Python (uses gh auth token automatically)
Write-Host ""
Write-Host "[4/5] Verifying repo access..."
python backlog/verify_github_token.py
if ($LASTEXITCODE -ne 0) { exit 1 }

# 5. Milestone audit
Write-Host ""
Write-Host "[5/5] Auditing milestones..."
python backlog/protect_and_audit.py

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Restart Cursor (Settings - Tools and MCP - github green dot)"
Write-Host "  2. Start Sprint 0: git checkout -b feature/T-02-02-postgres-init"
Write-Host "  3. Ask the agent to implement T-02-02 and open a PR with Closes #45"
Write-Host ""
Write-Host "Repo: https://github.com/smcshahid/ai-media-production-os"
