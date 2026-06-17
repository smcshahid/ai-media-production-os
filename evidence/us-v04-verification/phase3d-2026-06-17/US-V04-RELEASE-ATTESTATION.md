# US-V04 — Release Attestation Package (Phase 3D)

**Date:** 2026-06-17  
**Release:** `v0.13.0-phase3d`  
**Status:** **PASS** (attestation folded into release history)

---

## Attestation scope

US-V04 re-acceptance confirms production engine path per D-62, D-63, D-61:

| Check | Contract | Result |
|-------|----------|--------|
| Storyboard engine | `COMFYUI_WORKFLOW=flux_storyboard.json` | **PASS** |
| I2V enabled | `VIDEO_I2V_ENABLED=true` | **PASS** |
| Olares AI routing | `COMFYUI_HOST` → shared ComfyUI | **PASS** |
| Storyboard batch | 4 frames at MAX(version) (D-45) | **PASS** |
| VIDEO source | `comfyui_i2v` or `slideshow` + `fallback_reason` | **PASS** (see note) |
| Audit regression | `GET /audit` HTTP 200 | **PASS** |

---

## Production engine path

```
Idea (human)
  → Story (Ollama qwen3:14b)
  → Script (Ollama qwen3:14b)
  → Storyboard (ComfyUI Flux.1-dev, 1344×768, D-62)
  → Video (WAN 2.2 i2v with slideshow fallback, D-61)
  → Export ZIP (D-52)
```

---

## Verification commands

| Environment | Command |
|-------------|---------|
| Local | `make verify-usv04` |
| Olares | `deploy/k8s/usv04-verify/verify_usv04.sh` (via `make verify-all-olares`) |
| Release bundle | `make verify-all` (includes US-V04) |

---

## Evidence references

| Artifact | Path |
|----------|------|
| Phase 3A closure | `PHASE-3A-MISSION-CLOSURE.md` |
| Phase 3A US-V04 report | `docs/sprints/phase-3a-usv04-closure-report.md` |
| Quality runbook | `docs/runbooks/comfyui-quality.md` |
| Release manifest worker env | `deploy/release/manifest.yaml` |
| Local verify script | `deploy/dev/verify_usv04_local.ps1` |
| Olares verify script | `deploy/k8s/usv04-verify/verify_usv04.sh` |

---

## Decision records

- **D-61** — WAN 2.2 i2v with slideshow fallback
- **D-62** — Swappable storyboard engines (Flux default)
- **D-63** — Dev defaults: local app + Olares shared AI
- **D-73** — US-V04 release attestation package (Phase 3D)

---

## Note on i2v source

When WAN weights are missing or VRAM is exhausted, VIDEO metadata records `source=slideshow` with `fallback_reason`. This is **by design** (D-61). Release attestation accepts either:

- **Preferred:** `source=comfyui_i2v`
- **Acceptable:** `source=slideshow` with documented `fallback_reason`

Verify scripts emit `PASS` for i2v and `WARN` for slideshow fallback.

---

## Release history update

README and `docs/release/notes/v0.13.0-phase3d.md` reference US-V04 as part of official release verification gates.
