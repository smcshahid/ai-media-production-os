# AIMPOS-Spark — Phase Next Recommendation

**Date:** 2026-06-17  
**Prepared by:** Product Analyst · Verification Lead · Repository Custodian  
**Baseline:** Phase 3D CLOSED · Release candidate `v0.13.0-phase3d` · Olares-hosted deployment operational  
**Supersedes:** `ROADMAP-RECOMMENDATION.md` (pre–Phase 3D assessment)  
**Scope:** Planning only — no implementation authorized

---

## Executive summary

Phase 3D closed the platform maturity gap identified in the pre-3D roadmap: pinned images, distribution package, drift detection, `make verify-all`, US-V04 attestation, and operator runbooks. **The platform is release-ready; the binding constraint on creator value is no longer deployment — it is content scale (single scene) and GPU wall-clock.**

Evidence from 12+ pipeline runs, 447 cumulative audit events, and five-phase asset history on one project shows heavy **verification and iteration**, not multi-project production use. Phase 3B closed the highest-frequency **creator UX** gaps (diff, run history, error clarity). What remains open hurts **output length and commercial use**, not observability.

**Recommended next mission:** **Phase 4 — Multi-Scene Pilot (Product Depth)** with a mandatory **Release Adoption gate** (tag, Olares pinned deploy, Market submission) as WP-0 before scope expansion.

---

## Section 1 — Platform Assessment

### 1.1 Milestone inventory (completed)

| Milestone | Status | Release / evidence |
|-----------|--------|-------------------|
| M5 Visual MVP | **CLOSED** | `v0.4.0-usv01` |
| M6 Spark Full Phase 1 | **CLOSED** | `v0.7.0-usv02` |
| M7 Spark Full Phase 2 | **CLOSED** | `v0.12.0-usv03` |
| Phase 3A Trust & Visibility | **CLOSED** | US-V04, US-23b, bootstrap gate |
| Phase 3B Asset Intelligence | **CLOSED** | Export, diff, run history, PO UX |
| Phase 3C Platform Readiness | **CLOSED** | Olares web, audit pagination |
| Phase 3D Release Hardening | **CLOSED** | `v0.13.0-phase3d` RC, manifest, verify-all |

### 1.2 Generated projects and runs (evidence)

| Signal | Local dev | Olares cluster | Interpretation |
|--------|-----------|----------------|----------------|
| Projects | 1 seeded (`aa40cf32-…`) | 1 | Single-project model unchanged |
| Pipeline runs | 12 | 10+ | High iteration; acceptance + regression heavy |
| Audit events | 111 | 175 (paginated) / **447 cumulative** | Operational verification dominates log volume |
| Asset history stages | 5 (IDEA→VIDEO) | HTTP 200 | Full pipeline exercised repeatedly |
| Audit export size | ~60 KB JSON / ~43 KB CSV | — | Substantial event history per project |
| US-V01 reference run | Story edit, 2× SCRIPT regen, 2× STORYBOARD batch | — | Regen chains validate diff/history value |

**Inference:** The system is proven through **repeat end-to-end runs on one project**, not through diverse production workloads. Expanding **scene count** addresses the largest gap between platform capability and creator output.

### 1.3 Audit, asset history, and version diff

| Capability | State | Evidence |
|------------|-------|----------|
| Audit browser + export + pagination | **Operational** | Phase 3C: 175 events/page; D-69, D-66 |
| Asset history (5 stages) | **Operational** | Phase 3B: all stages HTTP 200 |
| Run history | **Operational** | D-68; 12 runs listed locally |
| Story/Script version diff | **Shipped, high value** | D-67; driven by Phase 3A PO regen pain; `textDiff.test.ts` |
| STORYBOARD / VIDEO diff | **Not shipped** | Phase 3B backlog; frame/video compare deferred |
| Run row asset summary | **Not shipped** | Phase 3B backlog #3 |

Version diff usage is **indirectly validated**: US-V01 and Phase 3A validation required comparing regen chains; US-30 was authorized specifically from PO findings, not backlog speculation.

### 1.4 Maturity scores (post–Phase 3D)

| Dimension | Score (1–5) | Δ vs pre-3D | Rationale |
|-----------|-------------|-------------|-----------|
| **Overall platform maturity** | **4.0** | +0.5 | RC ready; full pipeline + observability + release tooling |
| **Deployment maturity** | **4.0** | +1.0 | Manifest SSOT (D-71), `install.sh`, `deploy_release.sh`, drift check |
| **Operational maturity** | **4.5** | +1.5 | 5 runbooks, `verify-all`, checklists, nightly workflow scaffold |
| **Product maturity** | **3.0** | +0.5 | Pipeline complete; single scene + silent video cap creator value |

#### Deployment maturity (detail)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Reproducible install | 4/5 | Documented; manual SCP/SSH remains |
| Image traceability | 5/5 | `deploy/release/manifest.yaml` |
| Drift detection | 5/5 | `check_drift.sh` |
| One-click Market | 2/5 | **Not submitted** — top residual platform gap |
| Release tag on remote | 3/5 | RC ready; commit/tag/push pending authorization |

#### Operational maturity (detail)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Runbooks | 5/5 | Install, upgrade, recovery, verify, Olares ops |
| Consolidated verify | 5/5 | D-72 `make verify-all` |
| CI gates | 4/5 | Unit + manifest on PR; compose verify nightly only |
| PO launch path | 5/5 | Phase 3C: no `npm run dev`; Application CR running |

#### Product maturity (detail)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Core workflow | 5/5 | Idea → Video → Export attested (US-V02/V03, US-V04) |
| Creator transparency | 4/5 | Audit, history, diff, lineage, run list |
| Output scale | 1/5 | One scene only (Scope Freeze §1.2) |
| Identity / access | 1/5 | Bearer token (D-09) |
| Commercial readiness | 3/5 | Flux non-commercial default; Z-Image/RealVisXL available via env only |

---

## Section 2 — Evidence-Based Bottlenecks

### 2.1 Creator bottlenecks (ranked)

| Rank | Bottleneck | Status | Evidence | Value if fixed |
|------|------------|--------|----------|----------------|
| 1 | **Single scene only** | Open | MVP Scope Freeze; 12 runs on one scene | **High** — unlocks episodic/serial content |
| 2 | **GPU wall-clock (STORYBOARD + VIDEO)** | Open | `comfyui-quality.md`: ~48+ min i2v path | Medium — infra/model tuning; partial UX mitigation |
| 3 | **Silent video (no audio)** | Open | Spark Full exclusions; Phase 3B backlog | Medium — publishing readiness |
| 4 | **Token login UX** | Open | Phase 3C PO validation | Low for solo lab; blocks non-engineers |
| 5 | **Commercial engine selection** | Open | D-62 Flux license; env-only switch | Medium for commercial creators |
| 6 | **Slideshow vs i2v confusion** | Partially fixed | Phase 3B badge; D-73 WARN path | Low — mitigated |
| 7 | **No STORYBOARD/VIDEO diff** | Open | Phase 3B deferred | Medium — regen review for visual stages |
| 8 | **No stage progress ETA** | Open | D-59 WS + polling only | Low — cosmetic during GPU wait |
| 9 | **Approve/regenerate errors** | Mostly fixed | Phase 3B WP-5 | Low |
| 10 | **Export only at COMPLETED** | By design | D-52 | Low — correct gate |

### 2.2 Operational bottlenecks (ranked)

| Rank | Bottleneck | Status | Evidence |
|------|------------|--------|----------|
| 1 | **Olares Market not published** | Open | Phase 3C/3D backlog; RELEASE-READINESS 4/5 distribution |
| 2 | **Release not cut on remote** | Open | RC ready; tag/push pending authorization |
| 3 | **Cluster may still run `:dev` images** | Open until deploy | Phase 3D R-3D-01; drift check exists |
| 4 | **Manual SCP/SSH deploy** | Improved not eliminated | `deploy_release.sh` — still operator steps |
| 5 | **Compose verify not PR-blocking** | Open | `verify-nightly.yml` scaffold; no self-hosted runner |
| 6 | **WAN I2V weight provisioning** | Documented | `comfyui-quality.md` I2V vs T2V confusion |
| 7 | **Large audit export via proxy** | Mitigated | 1800s nginx timeout (Phase 3C) |
| 8 | **Branch protection absent** | Open | D-15 |
| 9 | **Launcher tile sync lag** | Documented | Phase 3C PO finding #1 |
| 10 | **Single-GPU sequencing** | Architectural | D-08 — not fixable without hardware |

**Resolved since pre-3D roadmap:** unpinned images (manifest), no `verify-all`, missing runbooks, US-V04 attestation gap.

### 2.3 Platform bottlenecks (ranked)

| Rank | Bottleneck | Impact | Evidence |
|------|------------|--------|----------|
| 1 | **Content model frozen at 1 scene** | Blocks product growth | BC 3.1 Deferred; all phase governance forbids multi-scene |
| 2 | **No multi-project tenancy** | Blocks studio use | Scope Freeze §1.2 |
| 3 | **No OIDC/RBAC** | Blocks team access | D-09; US-25 deferred |
| 4 | **No Neo4j / graph projector** | Low near-term | ADR 0003; PG edges sufficient today |
| 5 | **No asset restore/rollback/promote** | Compliance gap | Explicitly deferred Phase 2/3 |
| 6 | **No OpenTelemetry stack** | Observability ceiling | Request ID + audit only |
| 7 | **Audit offset-only pagination** | Scale at 500+ events/run | Phase 3C backlog |
| 8 | **WebSocket no replay** | Missed events on reconnect | D-59 out of scope |
| 9 | **MinIO orphan blobs (TD-25)** | Edge-case integrity | D-25 deferred compensation |
| 10 | **Integration CI gap** | Regression risk on infra | TD-CI-INT |

---

## Section 3 — Strategic Options

*Options re-evaluated **after Phase 3D** — Platform Maturity items partially delivered.*

---

### Option A — Platform Maturity (residual)

**Thesis:** Close the last mile of distribution and CI — Market publish, release cut execution, self-hosted compose verify, branch protection.

| Criterion | Assessment |
|-----------|------------|
| **Value** | **Medium** — enables adopters; does not change creator output |
| **Risk** | **Low** — no schema/workflow change |
| **Cost** | **S** (2–4 weeks) |
| **Dependencies** | Olares Market access; git tag authorization; optional self-hosted runner |
| **Governance impact** | Minimal — extends Phase 3D charter |

**Best when:** Primary goal is **external distribution** or handoff to non-engineer operators.

**Residual WPs:** Market submission · Olares pinned deploy attestation · Self-hosted CI compose verify · Branch protection (D-15)

---

### Option B — Product Depth

**Thesis:** Expand what one creator can produce — multi-scene pilot, character continuity, audio, visual-stage diff, in-app engine presets.

| Criterion | Assessment |
|-----------|------------|
| **Value** | **High** — addresses #1 creator bottleneck (single scene) |
| **Risk** | **High** — SCR required; Temporal workflow + D-37..D-51 touch |
| **Cost** | **L–XL** (10–18 weeks for multi-scene pilot) |
| **Dependencies** | Stable `v0.13.0-phase3d` deployed; GPU headroom scales with scene count |
| **Governance impact** | **Heavy** — SCR for pipeline semantics; new acceptance gate (US-V05?) |

**Best when:** Primary goal is **creator output quality and length** on proven platform.

**Scope discipline:** Pilot **2–3 scenes** first; defer character bible and audio to follow-on WPs.

---

### Option C — Studio Scale

**Thesis:** Keycloak/OIDC, multi-project, RBAC, notifications — prepare for teams.

| Criterion | Assessment |
|-----------|------------|
| **Value** | **Medium** for teams; **Low** for current solo Olares use |
| **Risk** | **High** — auth model change (D-09); all routes + WS auth |
| **Cost** | **L** (8–14 weeks) |
| **Dependencies** | Identity provider on Olares; security review |
| **Governance impact** | **Heavy** — SCR; verify script token plumbing changes |

**Best when:** Second creator or compliance audit **confirmed** — not evidenced today (1 project, 1 token, PO-only validation).

---

### Option comparison

| Dimension | A — Platform Maturity | B — Product Depth | C — Studio Scale |
|-----------|----------------------|-------------------|------------------|
| Creator value | Low | **High** | Low (near-term) |
| Time to value | **2–4 weeks** | 10–18 weeks | 8–14 weeks |
| Risk | **Low** | High | High |
| Evidence fit (post-3D) | Residual ops gaps | **#1 open creator bottleneck** | No multi-user signal |
| SCR required | No | **Yes** | Yes |

---

## Section 4 — Recommended Next Mission

### Mission name

**Phase 4 — Multi-Scene Pilot & Release Adoption**

### Rationale (evidence-based)

1. **Phase 3D closed Option A's core deliverables** — manifest, verify-all, runbooks, distribution package (`RELEASE-READINESS-REPORT.md` operational 5/5).
2. **12+ runs on one project** prove pipeline stability; next marginal value is **output scale**, not more observability.
3. **Phase 3B already addressed top UX bottlenecks** evidenced by PO validation (diff, run history, errors).
4. **Platform Maturity residual (Market, tag)** is **small enough for WP-0** — not a full phase.
5. **No evidence of multi-user demand** — Studio Scale lacks signal.

### Mission scope

| In scope | Out of scope |
|----------|--------------|
| WP-0 Release adoption gate | Full N-scene production (100+ scenes) |
| Multi-scene script breakdown (2–3 scenes) | Keycloak / RBAC |
| Workflow extension (SCR-governed) | Neo4j |
| Scene-scoped storyboard/video batches | Publishing to external platforms |
| Acceptance gate US-V05 (proposed) | Asset restore/rollback/promote |
| In-app commercial engine preset (UI) | Notifications / collaboration |
| Run history asset summary rows | Audio narration (defer to 4B) |

### Work packages

| WP | Title | Goal | Effort |
|----|-------|------|--------|
| **WP-0** | Release adoption gate | Tag `v0.13.0-phase3d`, Olares pinned deploy, drift=0, optional Market submit | S (1 week) |
| **WP-1** | SCR + governance | Multi-scene pipeline charter; D-records; frozen contract amendments | S |
| **WP-2** | Multi-scene script model | 2–3 scene Fountain; planner breaks approved story | M |
| **WP-3** | Workflow extension | Temporal stages per scene or scene loop; approval gates | L |
| **WP-4** | Scene-scoped assets | Storyboard/video per scene; export manifest v2 | L |
| **WP-5** | Creator UX | Engine preset UI (Z-Image/RealVisXL); run row summaries | S |
| **WP-6** | US-V05 acceptance | E2E Olares 2-scene run + verify scripts | M |

### Exit criteria

- [ ] WP-0: `v0.13.0-phase3d` tagged; Olares `check_drift` DRIFT=0; `verify-all-olares` FAIL=0
- [ ] SCR approved for multi-scene pipeline semantics
- [ ] Creator completes **2-scene** run: idea → story → script (2 scenes) → storyboard → video → export
- [ ] Export ZIP includes scene-differentiated assets; manifest version bumped
- [ ] No regression on single-scene Path A (US-V03 subset)
- [ ] API/web unit tests pass; new US-V05 verify FAIL=0 on Olares
- [ ] No open S1/S2 defects
- [ ] Phase 4 mission closure + evidence package

### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| GPU time multiplies by scene count | High | Cap pilot at 2 scenes; optional slideshow/i2v per scene |
| Workflow non-determinism (Temporal) | Medium | Follow US-09/US-18 retry patterns; fresh-run verify |
| Scope creep to full episodic series | High | SCR limits scene count; governance stop conditions |
| Market WP-0 delays Phase 4 start | Low | WP-0 parallelizable with SCR authoring |
| D-37..D-51 regression | Medium | Mandatory single-scene regression in US-V05 |

### Alternative path (if PO rejects multi-scene)

Execute **Option A only** as **Phase 4A — Distribution Close-out** (Market + CI compose verify). Defer Product Depth until PO confirms episodic content priority.

---

## Section 5 — Deferred Backlog

Items that **must remain deferred** until explicit SCR and governance brief — not backlog assumptions:

### Product / workflow

| Item | Classification | Rationale |
|------|----------------|-----------|
| Multi-scene (>3) / episodic series | Deferred | Phase 4 pilot scope cap |
| Character bible / continuity store | Deferred | Phase 3A forbidden; no PO signal yet |
| Audio narration / TTS | Deferred | Spark Full exclusions; silent video acceptable for pilot |
| STORYBOARD per-frame approve | Deferred | D-46 batch scope frozen |
| Asset restore / rollback / promote | Deferred | Phase 2/3 explicit exclusion |
| Publishing to YouTube/platforms | Future | Out of charter |
| Video editing / re-encoding | Future | Out of charter |
| NLE integration | Future | Scope Freeze §9 |

### Platform / architecture

| Item | Classification | Rationale |
|------|----------------|-----------|
| Keycloak / OIDC / RBAC (US-25 full) | Deferred | No multi-user evidence; D-09 sufficient for lab |
| Multi-project CRUD | Deferred | Scope Freeze §1.2; 1 project in all verify evidence |
| Neo4j / graph projector | Future | ADR 0003; PG lineage sufficient |
| OpenTelemetry full stack | Future | Request ID + audit meet current needs |
| WebSocket event replay | Deferred | D-59; collaboration trigger absent |
| New database / broker | Forbidden | Phase 3D stop conditions |
| Cloud inference / egress | Out of scope | Sovereignty principle |
| Notifications / collaboration | Future | No stakeholder request |

### Operational (low priority deferral)

| Item | Classification | Rationale |
|------|----------------|-----------|
| Audit keyset cursor pagination | Optional | Needed at 500+ events/run; currently 175/page OK |
| MinIO orphan compensation (TD-25) | Deferred | Edge case; benign dedup |
| Uvicorn plaintext banners (TD-19) | Cosmetic | |
| DB append-only triggers (TD-11) | Deferred | Domain rule sufficient for MVP |

### Completed — do not re-open as backlog

| Item | Closed in |
|------|-----------|
| Olares web entrance | Phase 3C (D-70) |
| Audit export + pagination | Phase 3B/3C (D-66, D-69) |
| Version diff (Story/Script) | Phase 3B (D-67) |
| Run history | Phase 3B (D-68) |
| Release manifest + verify-all | Phase 3D (D-71, D-72) |
| US-V04 attestation | Phase 3D (D-73) |
| Bootstrap migration gate | Phase 3A (D-65) |

---

## Evidence index

| Artifact | Path |
|----------|------|
| Phase 3D closure | `PHASE-3D-MISSION-CLOSURE.md` |
| Release readiness | `RELEASE-READINESS-REPORT.md` |
| Pre-3D roadmap | `ROADMAP-RECOMMENDATION.md` |
| Phase 3B runs/audit | `evidence/phase-3b-verification/local-2026-06-17/` |
| Phase 3C Olares | `PHASE-3C-MISSION-CLOSURE.md` |
| US-V04 attestation | `evidence/us-v04-verification/phase3d-2026-06-17/` |
| Release manifest | `deploy/release/manifest.yaml` |
| Scope contract | `MVP Scope Freeze.md` |
| GPU timing | `docs/runbooks/comfyui-quality.md` |

---

## Document control

| Field | Value |
|-------|-------|
| Document ID | AIMPOS-PHASE-NEXT-001 |
| Version | 1.0 |
| Baseline | Phase 3D CLOSED · `v0.13.0-phase3d` RC |
| Next review | Upon Phase 4 governance brief ACCEPT or SCR approval |

*Planning only. No implementation, commit, tag, or push authorized by this document.*
