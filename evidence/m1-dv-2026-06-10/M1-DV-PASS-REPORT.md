# M1-DV PASS Report

**Date:** 2026-06-10  
**Host:** `olares@10.0.0.34` (k3s v1.33.3+k3s1)  
**Namespace:** `aimpos-mwayolares`  
**Authority:** D-31, D-36, `docs/runbooks/m1-dv-execution.md`  
**Supersedes:** `M1-DV-FAIL-REPORT.md` (sessions 1–3 partial)

---

## Verdict

**M1-DV: PASS**

Closes deployment validation for **US-02 (live Olares)**, **US-06 (live GPU smokes)**, **EPIC-01**, and **FEAT-INFRA** rollup per D-31 / `definition-of-done.md` §M1-DV.

Sprint 3 (US-12+) is **unblocked** pending M2 from Sprint 2.

---

## Governance attestation — minimum deployment bundle

### Question

Can M1-DV close with only **PostgreSQL, MinIO, Redis, API** on Olares, consuming **shared Ollama + shared ComfyUI**, omitting **Temporal, Worker, Web**?

### Answer: **Yes — governance-safe**

| Source | Requirement | How satisfied |
|--------|-------------|---------------|
| **D-31 / M1-DV gate** | US-06 smoke on Olares; US-02 live; EPIC-01/FEAT-INFRA close | Phases A–D below — no Temporal/worker/web in gate table |
| **EPIC-01 AC** | Runnable stack: Postgres, MinIO, Redis, Ollama, ComfyUI, API, `/health`, smokes | 4 AIMPOS services + 2 shared AI; compose one-command proof via **S1-SW** |
| **US-02 AC** | 9 containers healthy; `/health` 200; MinIO round-trip; aimpos-spark network | **Split attestation:** S1-SW proved 9-service compose on dev (`Sprint1_Status.md`); M1-DV proved **Olares functional equivalent** (k3s hybrid — Olares has no host Docker) |
| **US-06 AC** | Ollama &lt;30s; ComfyUI PNG → MinIO; GPU sequencing | Live smokes session-4 |
| **US-03 AC** | `/health` includes temporal | Deferred at S0 closure; current API probes postgres/redis/minio only — **not a M1-DV blocker** |
| **FEAT-INFRA** | Child stories closed | US-04/03/05/01 closed S0/S1-SW; US-02/US-06 closed this session |
| **Sprint1_Status.md** | M1-DV exit criteria | All items below PASS |

**Explicitly omitted (Sprint 2+ / not in M1-DV gate):** Temporal, Worker, Web SPA, Marketplace packaging.

**Hybrid AI (inventory 2026-06-10):** `USE EXISTING` shared Ollama (`qwen3:14b`) and ComfyUI (`:8190`).

---

## Deployment topology (session 4)

| Component | Deployment | Endpoint |
|-----------|------------|----------|
| PostgreSQL | `aimpos-postgres` (Helm/bitnami) | `aimpos-postgres:5432` |
| MinIO | `aimpos-minio` (Helm/bitnami) | `aimpos-minio:9000` |
| Redis | `aimpos-redis-master` (Helm/bitnami) | `aimpos-redis-master:6379` |
| API | `aimpos-api` Deployment | `aimpos-api:8000` |
| Ollama | **Shared** `ollamaserver-shared` | `:11434` |
| ComfyUI | **Shared** `comfyuisharev2server-shared` | `:8190` |

**Artifacts:** `deploy/k8s/m1-dv/`  
**API image:** `docker.io/library/aimpos-api:m1-dv` (imported via `nerdctl load`)

---

## Phase results

| Phase | Criterion | Result | Evidence |
|-------|-----------|--------|----------|
| **A** | `GET /health` → 200; postgres/redis/minio ok | **PASS** | `logs/session-4/health.json` |
| **A** | MinIO upload/download round-trip | **PASS** | `logs/session-4/minio-roundtrip.txt` |
| **B** | `test_ollama.py --require-live` (`qwen3:14b`, &lt;30s) | **PASS** (1.6s) | `logs/session-4/test_ollama.txt` |
| **C** | `test_comfyui.py --require-live` → AIMPOS MinIO PNG | **PASS** (216 KB PNG) | `logs/session-4/test_comfyui.txt` |
| **D** | Zero-egress capture (T-02-06 adapted) | **PASS** | `logs/session-4/zero-egress.txt` |

**Pod snapshot:** `logs/session-4/pods.txt`

---

## Notes

1. **Redis Helm fix:** Bitnami chart default RediSearch modules removed from `redis-values.yaml` (`commonConfiguration` override) — `bitnamilegacy/redis` lacks module `.so` files.
2. **ComfyUI smoke:** Cluster MinIO credentials passed via `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` env (`test_comfyui.py` now honors env override). PNG stored at `aimpos-hot-assets/smoke/comfyui/sdxl_storyboard.png` on **Olares AIMPOS MinIO**.
3. **US-02 “9 containers”:** Literal compose proof remains on **S1-SW**; Olares proof is the **minimum raw K8s app plane + shared AI** path approved in planning review.

---

## Sign-off

| Role | Status |
|------|--------|
| Platform (M1-DV execution) | PASS — 2026-06-10 session 4 |
| PO / formal issue close | Pending GitHub issue updates |
