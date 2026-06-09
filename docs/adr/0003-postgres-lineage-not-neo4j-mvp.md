# ADR 0003 — PostgreSQL Lineage Edges in MVP (Neo4j Deferred)

**Status:** Accepted (records a decision already frozen)  
**Date:** 2026-06-09  
**Source of truth:** [MVP Scope Freeze.md](../../MVP%20Scope%20Freeze.md) §5, [Enterprise Knowledge Graph.md](../../Enterprise%20Knowledge%20Graph.md)

## Context

The full platform specifies Neo4j for the enterprise knowledge graph. The MVP needs lineage/provenance but must minimize moving parts.

## Decision

Represent asset lineage as a `lineage_edges` table in PostgreSQL for the Visual MVP. Defer Neo4j to Phase 1.

## Consequences

- One fewer service to run and operate in the MVP.
- Lineage queries are SQL joins, not Cypher; acceptable for single-project, single-scene scope.
- Migration path to Neo4j is a future projector service (Repository Structure §8).

This ADR records an already-frozen decision; it does not introduce new architecture.
