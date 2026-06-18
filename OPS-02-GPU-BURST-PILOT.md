# OPS-02 — GPU Burst Pilot Operations Package

**Date:** 2026-06-18  
**Mission:** Phase 8 WP-7 (preparation only — **no implementation authorized**)  
**Baseline:** `v0.17.1-phase7-character-hardening`  
**Study authority:** GPU Burst Study (WP-7 closure)

---

## 1. Pilot objectives

Validate that AIMPOS can remain **Olares-first** while reducing GPU-bound acceptance and production runtimes by **≥50%** for multi-scene workloads using optional manual burst capacity.

| Objective | Success criterion |
|-----------|-------------------|
| Runtime reduction | ≥50% on 3-scene STORYBOARD parallel or i2v parallel path |
| Sovereignty | Olares retains Ollama, Temporal, MinIO, export, audit |
| Cost control | Documented spend cap per run; operator approval gate |
| Operational safety | No production data on burst without encrypted transfer policy |
| Rollback | Burst disabled → full Olares path unchanged |

---

## 2. Recommended architecture (Option B — Manual Burst)

```
┌─────────────────────────────────────────────────────────┐
│ Olares (authoritative)                                   │
│  API · Web · Worker (orchestration) · Temporal · MinIO   │
│  Ollama (STORY/SCRIPT) · espeak narration · Export       │
└───────────────────────┬─────────────────────────────────┘
                        │ optional ComfyUI jobs
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Burst GPU pod (RunPod / Vast — operator provisioned)     │
│  ComfyUI STORYBOARD + VIDEO only · ephemeral · no DB     │
└─────────────────────────────────────────────────────────┘
```

**Rejected:** Full cloud rendering (Option D) — sovereignty and governance cost too high.

---

## 3. Success metrics

| Metric | Baseline (Olares) | Target (burst) | Measurement |
|--------|-------------------|----------------|-------------|
| 3-scene slideshow E2E | ~9 min | ≤4 min (~56%) | US-V09 timing log |
| 3-scene i2v episode (parallel) | ~156 min | ≤52 min (~67%) | Production export timer |
| Cost per 3-scene i2v | $0 | ≤$0.82 | GPU-COST-MODEL |
| Verification cycle add-on | $0 | ≤$1.50 | Operator ledger |
| Sovereignty incidents | 0 | 0 | Audit review |

---

## 4. Cost model (summary)

Source: `GPU-COST-MODEL.md`, `GPU-BURST-RECOMMENDATION.md`.

| Profile | Monthly burst spend | Notes |
|---------|---------------------|-------|
| Lab / acceptance | **$8–18** | Parallel STORYBOARD smoke |
| Heavy production | $60–350 | 3-scene i2v parallel |
| Per 3-scene i2v export | **$0.28–0.82** | RTX 4090 class, ~48 min parallel |

**Governance cap:** Operator must set `BURST_BUDGET_USD` before session; abort if exceeded.

---

## 5. Runtime targets

| Workload | Olares serial | Burst target | Method |
|----------|---------------|--------------|--------|
| STORYBOARD 3-scene | 9 min | 4 min | 3× parallel ComfyUI pods |
| VIDEO i2v 3-scene | 156 min | 48 min | Parallel scene dispatch |
| STORY/SCRIPT | <2% of i2v | N/A | Stay on Olares Ollama |
| Narration | unchanged | unchanged | Stay on Olares espeak |

Optional: Lightning LoRA on burst pod for additional i2v speed (document only — not in pilot scope).

---

## 6. Operational procedures

### 6.1 Pre-pilot checklist

- [ ] Olares cluster at manifest pins (`deploy/release/manifest.yaml`)
- [ ] US-V09 PASS on Olares (platform attestation)
- [ ] Operator trained on `docs/operations/OLARES-OPERATIONS-GUIDE.md`
- [ ] Burst provider account + SSH tunnel documented
- [ ] `BURST_BUDGET_USD` and session owner recorded in evidence folder

### 6.2 Burst session (manual)

1. Provision GPU pod (RTX 4090 or equivalent); install ComfyUI matching worker workflow version.
2. Configure worker `COMFYUI_HOST` tunnel to burst endpoint (**acceptance project only**).
3. Run bounded path (3-scene STORYBOARD or i2v); capture timestamps in evidence log.
4. Terminate pod; restore worker env to Olares-local ComfyUI.
5. Run drift check; confirm no manifest/Alembic change.

### 6.3 Abort conditions

- Cost exceeds budget mid-run
- ComfyUI workflow version mismatch
- Export manifest version regression
- Any PII or production project ID on burst pod

---

## 7. Governance controls

| Control | Mechanism |
|---------|-----------|
| No auto-provision | Manual operator action only |
| No cloud DB | Burst stateless; Olares authoritative |
| Evidence required | `evidence/gpu-burst-pilot/` per session |
| SCR gate | Implementation requires new SCR post-pilot |
| Release gate | Pilot results do not change semver without closure |

---

## 8. Pilot readiness assessment

| Item | Status |
|------|--------|
| Study complete | **YES** |
| Cost model | **YES** |
| Runtime targets documented | **YES** |
| Operational procedures | **YES** (this document) |
| Implementation | **NOT AUTHORIZED** |
| Cloud deployment | **NOT AUTHORIZED** |

**Verdict:** Package is **ready to execute** when governance authorizes a bounded GPU Burst Pilot mission (post Phase 8).

---

## 9. References

- [GPU-BURST-RECOMMENDATION.md](GPU-BURST-RECOMMENDATION.md)
- [GPU-COST-MODEL.md](GPU-COST-MODEL.md)
- [GPU-PERFORMANCE-BASELINE.md](GPU-PERFORMANCE-BASELINE.md)
- [PHASE-GPU-BURST-CLOSURE.md](PHASE-GPU-BURST-CLOSURE.md)
