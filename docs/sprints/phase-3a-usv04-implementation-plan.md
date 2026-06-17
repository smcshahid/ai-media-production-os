# US-V04 — Flux + WAN re-acceptance (implementation plan)

**Status:** **IMPLEMENTED** (verification-only)  
**Baseline:** D-62/D-63 quality upgrade post-M7

## Scope

Re-attest the production-quality GPU path without product code changes:

| Check | Method |
|-------|--------|
| Worker env: `flux_storyboard.json`, `VIDEO_I2V_ENABLED=true` | docker exec / k8s deploy env |
| STORYBOARD batch: 4 frames at max version | SQL |
| Migration 0003 indexes | SQL |
| VIDEO `metadata.source` | SQL (`comfyui_i2v` or documented slideshow fallback) |
| Audit API regression | `GET /audit` |

## Scripts

- `deploy/dev/verify_usv04_local.ps1` — local D-63 stack  
- `deploy/k8s/usv04-verify/verify_usv04.sh` — Olares cluster deploy

## Note on i2v

WAN i2v requires weights on Olares ComfyUI. Slideshow fallback is **acceptable** with documented `fallback_reason`; mission PASS requires worker i2v enabled + Flux storyboard batch stored.
