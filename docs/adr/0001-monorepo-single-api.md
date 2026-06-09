# ADR 0001 — Monorepo with a Single FastAPI Application

**Status:** Accepted (records a decision already frozen)  
**Date:** 2026-06-09  
**Source of truth:** [Repository Structure.md](../../Repository%20Structure.md), [System Architecture.md](../../System%20Architecture.md)

## Context

Visual MVP is built by a solo founder. The full platform envisions many services, but the MVP needs the smallest deployable surface.

## Decision

Use a single monorepo with one FastAPI application (`api/`), one Temporal worker (`worker/`), and one React SPA (`web/`). Bounded contexts are folders inside `api/domain/`, not separate services.

## Consequences

- Simpler local dev and deploy (one compose stack).
- Service boundaries enforced by folder rules (coding-standards §23), not network boundaries.
- Future extraction is a folder-to-service move; `packages/` shared types prevent drift.

This ADR records an already-frozen decision; it does not introduce new architecture.
