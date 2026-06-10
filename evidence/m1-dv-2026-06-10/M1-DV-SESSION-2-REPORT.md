# M1-DV Session 2 — 2026-06-10 (Olares hybrid)

**Host:** `olares@10.0.0.34`  
**Commit:** (working tree — D-36 applied)  
**Classification:** **FAIL** (partial AI plane PASS; full M1-DV not closed)  
**Evidence:** `evidence/m1-dv-2026-06-10/logs/session-2/`

---

## Governance applied

- **D-36** configuration correction: `llama3.1:13b` → `qwen3:14b` (no SCR)
- M1-DV package updated: `docs/runbooks/m1-dv-execution.md`

---

## Phase results

| Phase | Step | Result | Evidence |
|-------|------|--------|----------|
| **A** | AIMPOS 9-service deploy on Olares | **NOT RUN** | Olares uses k3s; dedicated compose not deployed |
| **A** | `GET /health` US-02 proof | **NOT RUN** | Blocked on Phase A |
| **B** | Ollama `qwen3:14b` live inference | **PASS** | `01-ollama-smoke.txt` — 8.0s, response `OK` |
| **B** | `test_ollama.py` via SSH tunnel | **TIMEOUT** | In-cluster equivalent PASS accepted for Phase B |
| **C** | `verify-comfyui.sh` | **PASS** | `02-comfyui-verify.txt` — queue 200, SDXL present |
| **C** | `test_comfyui.py` PNG + MinIO | **NOT RUN** | Requires AIMPOS MinIO (`aimpos-hot-assets`) |
| **D** | Zero egress #49 | **NOT RUN** | Blocked on Phase A |

---

## PASS criteria met (partial)

- Shared Ollama reachable; **`qwen3:14b`** generates text in &lt;30s (with `num_predict=128` for thinking model).
- Shared ComfyUI `/queue` HTTP 200; **`sdxl_base_1.0.safetensors`** visible.

## Blockers for M1-DV close

1. **Phase A** — Deploy AIMPOS app/data plane on Olares (Postgres, MinIO, Redis, Temporal, API, worker).
2. **Phase C** — Run `test_comfyui.py --require-live` with AIMPOS MinIO endpoint after Phase A.
3. **Phase D** — Zero-egress capture on deployed stack.

---

## Gate status

| Item | Status |
|------|--------|
| M1-DV | **OPEN** |
| US-12 / US-13 / US-09 | **NOT AUTHORIZED** |

## Next session

1. Deploy AIMPOS stack on Olares (chart or compose if available).
2. Re-run Phase A → D per `docs/runbooks/m1-dv-execution.md`.
3. Deliver **M1-DV-PASS-REPORT.md** only when all phases pass.
