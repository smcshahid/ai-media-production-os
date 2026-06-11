# US-17 Acceptance Package — Local Verification

**Date:** 2026-06-11  
**Baseline:** `v0.3.5-us16` (`4f52bb5`)  
**Implementation:** US-17 storyboard batch review gallery

---

## Test gates (local)

| Suite | Result |
|---|---|
| API unit | **81 passed** (+3 US-17) |
| Worker unit | **36 passed** (+3 US-17) |
| Web unit | **23 passed** (+3 US-17) |

Log: `logs/pytest-api-us17.txt`, `logs/pytest-worker-us17.txt`, `logs/vitest-us17.txt`

---

## AC mapping (local evidence)

| AC | Local evidence |
|---|---|
| AC-1 Grid 4 images | `web/src/tests/storyboardReview.test.ts`; `ReviewPage.tsx` 2×2 grid |
| AC-2 Lightbox | `StoryboardLightbox.tsx` component |
| AC-3 Approve → COMPLETED | API approve route (existing US-08); workflow COMPLETED path unchanged |
| AC-4 Reject → regen | `test_pipeline_regenerate.py` STORYBOARD; `test_storyboard_regen.py` D-47 |
| AC-5 AI badge | `ReviewPage.tsx` badge on storyboard tiles |

Olares E2E required for closure — see `olares-2026-06-11/US-17-ACCEPTANCE-PACKAGE.md`.
