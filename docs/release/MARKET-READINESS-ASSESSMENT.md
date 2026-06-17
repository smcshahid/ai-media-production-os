# Olares Market Readiness Assessment

**Date:** 2026-06-17  
**Release:** `v0.13.0-phase3d`  
**Assessor:** Product Architect · Repository Custodian

---

## Executive summary

AIMPOS is **partially ready** for Olares Market submission. The web entrance chart, OlaresManifest, Application CR, and install documentation are complete. **Full-stack one-click install is not ready** — the Market package would deploy the web entrance only; backend stack (API, worker, postgres, minio, redis, temporal) still requires separate M1-DV/story deploys.

**Submission readiness:** **Yellow** — submit web chart with documented backend prerequisite, or defer until unified full-stack chart exists.

---

## Packaging inventory

| Component | Present | Location | Market-ready? |
|-----------|---------|----------|---------------|
| OlaresManifest | Yes | `deploy/olares/aimpos/OlaresManifest.yaml` | Yes (v0.13.0) |
| Helm chart | Yes | `deploy/olares/aimpos/` | Partial (web only) |
| Application CR template | Yes | `templates/application.yaml` | Yes |
| Web + ingress templates | Yes | `templates/web.yaml`, `ingress.yaml` | Yes |
| Pinned image refs | Yes | `values.yaml` → `v0.13.0-phase3d` | Yes |
| Install script | Yes | `install.sh` | Manual backend dep |
| Dependency doc | Yes | `DEPENDENCIES.md` | Yes |
| Icon/branding | Default Olares placeholder | CDN default icon | **Gap** — custom icon |
| Backend unified chart | **No** | M1-DV scripts scattered | **Gap** |
| GPU/shared AI bundling | **No** | External Olares services | Documented only |

---

## Gap analysis

| ID | Gap | Severity | Remediation | Effort |
|----|-----|----------|-------------|--------|
| G-M01 | Web-only chart; backend not in Market package | **High** | Unified Helm umbrella chart or Market dependency declaration | L |
| G-M02 | Default placeholder icon | Low | Custom AIMPOS icon asset | S |
| G-M03 | Manual `docker save` / `ctr import` for API/worker | **High** | Registry push or Olares image bundle in chart | M |
| G-M04 | Shared Ollama/ComfyUI not declared as chart dependency | Medium | Document in Market listing; optional subchart | M |
| G-M05 | No automated Market CI validation | Medium | Olares Studio import smoke | S |
| G-M06 | `requiredMemory`/`limitedMemory` may be low for full stack | Low | Web-only values OK; revise if bundling backend | S |
| G-M07 | License metadata not in manifest | Low | Add OpenRAIL/usage notes for Flux vs Z-Image | S |

---

## Submission readiness checklist

| Requirement | Status |
|-------------|--------|
| Chart validates (`helm template`) | Assumed PASS — operator verify before submit |
| OlaresManifest schema valid | Yes |
| Version aligned with release | Yes (0.13.0) |
| Install guide for end user | Yes (`INSTALLATION-GUIDE.md`) |
| Upgrade path documented | Yes |
| Verify script post-install | Yes (`make verify-all-olares`) |
| Full stack without SSH | **No** |
| Privacy/zero-egress narrative | Yes (sovereign local AI) |

---

## Recommended Market strategy

### Option 1 — Submit web entrance now (recommended short-term)

- Package `deploy/olares/aimpos/` as dev/Market app
- Listing clearly states: **requires `aimpos-mwayolares` backend stack**
- Link to `INSTALLATION-GUIDE.md`
- **Risk:** User confusion if backend missing
- **Value:** Launcher tile distribution for existing operators

### Option 2 — Defer until full-stack chart (recommended medium-term)

- Build umbrella chart: postgres, minio, redis, temporal, api, worker, web
- Single Market install
- **Effort:** 4–6 weeks
- **Value:** True one-click adoption

### Option 3 — Hybrid Market dependency

- Declare backend as separate Olares app dependency (if platform supports)
- Requires Olares platform capability verification

---

## Submission readiness report

| Dimension | Score (1–5) |
|-----------|-------------|
| Documentation | 5 |
| Web chart quality | 4 |
| Full-stack packaging | 2 |
| Image distribution | 3 |
| Operator verify path | 5 |
| **Overall Market readiness** | **3.5 / 5** |

**Verdict:** Proceed with **Option 1** for early adopters who already run M1-DV stack; plan **Option 2** as Phase 4A follow-on if Market adoption is strategic priority.

---

## Related documents

- `deploy/olares/aimpos/README.md`
- `deploy/olares/aimpos/DEPENDENCIES.md`
- `docs/release/INSTALLATION-GUIDE.md`
