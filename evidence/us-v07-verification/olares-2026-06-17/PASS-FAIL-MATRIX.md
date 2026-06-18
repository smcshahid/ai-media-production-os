# US-V07 Olares PASS/FAIL Matrix — Final

**Date:** 2026-06-18  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Images:** `usv07-phase6`  
**Alembic head:** `0005`

---

## Primary E2E (`summary-e2e.txt`)

| Path | Result | Run ID | Episode | Notes |
|------|--------|--------|---------|-------|
| A | **PASS** | `16d4b266-c088-4b8a-baf8-188f83470be0` | ep 23 | manifest v4 |
| B | **PASS** | `cad81163-76e2-4f03-9f6f-30299e080f66` | ep 24 | manifest v4, 3 scenes |
| C1 | **FAIL** | `69c705a6-b7cd-4f13-90d6-c3e8d78cec17` | ep 25 | orphaned — empty result |
| C2 | **PASS** | `1e4f8f0a-1e77-4521-a91f-002355b688ef` | ep 26 | manifest v4 |
| D | **PASS** | legacy runs | — | v1/v2/v3 ladder |
| E | **PASS** | ref A | — | governance reads |
| **Overall** | **FAIL=1** | | | blocked on C1 |

---

## PATH C1 supplement (`path-c1/summary-c1.txt`)

| Path | Result | Run ID | Episode | Notes |
|------|--------|--------|---------|-------|
| C1 | **PASS** | `1e9e6246-b059-4107-b50d-c1626d5d8e84` | ep 28 | manifest v4, FAIL=0 |

---

## Final acceptance matrix (governance)

| Path | Primary | Supplement | **Final** |
|------|---------|------------|-----------|
| A | PASS | — | **PASS** |
| B | PASS | — | **PASS** |
| C1 | FAIL | PASS | **PASS** |
| C2 | PASS | — | **PASS** |
| D | PASS | — | **PASS** |
| E | PASS | — | **PASS** |
| Local automated | PASS | — | **PASS** |
| **US-V07** | | | **ACCEPTED** |

---

## Defect disposition

| Defect | Severity | Status |
|--------|----------|--------|
| C1 E2E orphan / overlap | SEV-3 | **CLOSED** (supplement + script fix) |
| SEV-1 | — | **0 open** |
| SEV-2 | — | **0 open** |
