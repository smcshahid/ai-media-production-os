# Sprint 1 — Infrastructure Validation: Status Tracker

**Started:** 2026-06-09 · **Branch:** `main` (local work, no PR yet)
**Governance:** SCR-2026-001 / **D-31** — track **S1-SW** and **M1-DV** separately
**Handoff:** [`docs/sprints/sprint-1-handoff.md`](./docs/sprints/sprint-1-handoff.md)

---

## S1-SW — Sprint 1 software exit

| Item | Status | Notes |
|------|--------|-------|
| TD-21 CI workflow | ✅ | `.github/workflows/ci-api.yml` |
| #62 T-06-03 GPU sequencing (`worker/README.md`) | ✅ | D-08; `gpu-sequencing.md` runbook |
| #69 least-privilege compose env | ✅ | |
| #70 hermetic smoke tests | ✅ | postgres + minio |
| #71 README port map | ✅ | |
| #44 T-02-01 full compose | ✅ | `docker compose config` valid |
| T-02-04 compose/config authoring | ✅ | `ollama-init`, `models.json` |
| T-02-05 runbooks + README | ✅ | local / olares / gpu-sequencing; smoke index |
| T-06-01 `test_ollama.py` | ✅ | SKIP verified dev host; live = M1-DV |
| T-06-02 workflow + `test_comfyui.py` | ✅ | `sdxl_storyboard.json`, D-03; SKIP verified |
| D-02, D-03, D-08 recorded | ✅ | |

**S1-SW exit:** ✅ **closed** (2026-06-09) — software track complete; Sprint 2 may begin.

**Sprint 2 entry:** Allowed (S1-SW passed; M1-DV not required).

---

## M1-DV — Deployment validation (GPU / Olares)

| Item | Status | Notes |
|------|--------|-------|
| #47 T-02-04 live `ollama list` | ✅ | `qwen3:14b` on shared Ollama (D-36) |
| #60 T-06-01 Ollama smoke (live) | ✅ | `logs/session-4/test_ollama.txt` |
| #61 T-06-02 ComfyUI smoke (live) | ✅ | `logs/session-4/test_comfyui.txt` → AIMPOS MinIO |
| #48/#49 Olares docs + deploy proof | ✅ | `deploy/k8s/m1-dv/` + session-4 evidence |
| #49 T-02-06 zero-egress verification | ✅ | `logs/session-4/zero-egress.txt` |
| US-06 / US-02 / EPIC-01 / FEAT-INFRA close | ✅ | `M1-DV-PASS-REPORT.md` 2026-06-10 |

**M1-DV exit:** ✅ **closed** (2026-06-10 session 4) — raw K8s hybrid on Olares.

**Sprint 3 entry:** Blocked until M1-DV passes (and M2 from Sprint 2).

---

## S1-SW verification record (closure)

| Check | Result |
|-------|--------|
| API health | 200 healthy (session 1) |
| API unit tests | 47 passed (session 1) |
| Web build/lint/test | clean / 7 passed (session 1) |
| Compose config | valid (session 1) |
| Postgres smoke (hermetic) | PASS (session 1) |
| MinIO smoke (hermetic) | PASS (session 1) |
| `test_ollama.py` authored | PASS — SKIP exit 2 on dev host (not fabricated) |
| `test_ollama.py --require-live` | FAIL exit 1 when Ollama down (M1-DV mode correct) |
| `test_comfyui.py` authored | PASS — SKIP exit 2 on dev host |
| D-03 workflow pin | `configs/comfyui/workflows/sdxl_storyboard.json` |
| Runbooks | local-development, olares-deployment, gpu-sequencing |
| README smoke index | updated |

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-06-09 | Sprint 1 session 1 |
| 1.1 | 2026-06-09 | SCR-2026-001: S1-SW / M1-DV tracker split |
| 1.2 | 2026-06-09 | S1-SW closed: T-06-01/02 scripts, D-03, runbooks |
| 1.3 | 2026-06-10 | M1-DV closed: raw K8s hybrid Olares; PASS report session-4 |
