"""PostgreSQL persistence layer — SQLAlchemy models and repositories.

PostgreSQL is the system of record (System Architecture, ADR-0003). SQLAlchemy
models live here only and are never imported by ``api/app/domain/`` (domain
purity rule, coding-standards.md §32).
"""
