# ADR 0002 — Temporal over a Custom State Machine

**Status:** Accepted (records a decision already frozen)  
**Date:** 2026-06-09  
**Source of truth:** [Technology Recommendations.md](../../Technology%20Recommendations.md), [Workflow Architecture.md](../../Workflow%20Architecture.md)

## Context

The pipeline (Idea → Story → Script → Storyboard) needs durable, resumable orchestration with human approval gates and survival across worker restarts (SC-06).

## Decision

Use Temporal for the `SparkPipelineWorkflow`. Do not build a custom DB-backed state machine.

## Consequences

- Durability, retries, and signal-based approvals come from Temporal.
- Workflow code must be deterministic; side effects live in activities (coding-standards §124).
- Learning curve is the steepest in the plan — scheduled for Sprint 2 (US-07) after infra is validated.

This ADR records an already-frozen decision; it does not introduce new architecture.
