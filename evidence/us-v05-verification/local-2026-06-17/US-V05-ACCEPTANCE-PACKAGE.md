# US-V05 Multi-Scene Pilot — Acceptance Package

**Date:** 2026-06-17  
**Baseline:** `v0.13.0-phase3d` → Phase 4 multi-scene pilot  
**SCR:** SCR-2026-002 (ACCEPTED)  
**Authority:** Phase 4 Multi-Scene Pilot mission

---

## Acceptance summary

| Criterion | Result | Evidence |
|-----------|--------|----------|
| 2-scene workflow (domain/export) | **PASS** | `api/tests/unit/test_multi_scene_export.py` |
| 3-scene workflow (validation) | **PASS** | `worker/tests/unit/test_fountain_validate.py` |
| Single-scene backward compatibility | **PASS** | Existing export test; default `scene_count=1` |
| Audit (scene_index in payload) | **PASS** | Activity audit payloads extended |
| History (scene sort) | **PASS** | `asset_history/resolver.py` scene-aware sort |
| Diff (Story/Script) | **PASS** | Unchanged text diff (D-67) |
| Lineage (export chain) | **PASS** | `resolve_export_files` multi-scene paths |
| Export manifest v2 | **PASS** | `manifest.py` v2 for multi-scene ZIP |
| Local verification | **PASS** | API 115+, worker 56, web 43 tests |
| Olares verification | **PARTIAL** | Operator deploy + E2E pending (SSH/cluster) |

---

## Architecture summary

- **One STORY**, **one SCRIPT** (1–3 Fountain scenes), **per-scene STORYBOARD batch** (4 frames) and **VIDEO**.
- Scene semantics via `metadata_json.scene_index` / `scene_count` (D-75).
- `pipeline_runs.scene_count` set at start; `current_scene_index` during scene loop (D-77).
- Temporal workflow: STORY → SCRIPT → loop(scenes){ STORYBOARD → VIDEO } (D-76/D-78).
- Export: flat v1 layout for single-scene; `scenes/scene_XX/` + manifest v2 for multi-scene.

---

## Schema changes (Alembic 0004)

| Change | Type |
|--------|------|
| `pipeline_runs.scene_count` | Additive column |
| `pipeline_runs.current_scene_index` | Additive column |
| `approvals.scene_index` | Additive column |
| STORYBOARD unique index | Extended with `scene_index` |

**Migration strategy:** `alembic upgrade head`; legacy rows treated as scene 1.

---

## Verification commands

```powershell
# Local
./deploy/dev/verify_phase4_local.ps1

# API / worker / web only
cd api && python -m pytest tests/unit -q
cd worker && python -m pytest tests/unit -q
cd web && npm run test -- --run
```

```bash
# Olares (from networked host with kubectl)
./deploy/k8s/usv05-verify/verify_usv05.sh
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| GPU wall-clock scales with scenes | Pilot capped at 3 scenes |
| Script agent may miss exact scene count | `expected_scene_count` validation gate |
| Olares E2E not run from automation host | Operator verify script + deploy 0004 |

---

## Lessons learned

- Metadata + read-layer extension preserved lineage/history/audit without redesign (stop conditions not triggered).
- Stage-only Temporal signals remain compatible; scene context lives in DB/workflow state.
- Export v1/v2 split preserves single-scene consumer compatibility.

---

## Recommendation for Phase 5

Proceed with **Platform Maturity** (release adoption, Olares operator runbook) **or** bounded **episode model** only after US-V05 Olares E2E attestation on 2- and 3-scene runs.
