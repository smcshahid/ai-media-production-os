"""Async Redis client builder.

A pure builder (no global client, no env reads) mirroring the DB session layer:
the app factory wires it to settings and owns its lifecycle. Sprint 0 only needs
a connectivity check for ``/health``; richer cache/pub-sub usage arrives later.
"""

from __future__ import annotations

from redis.asyncio import Redis


def build_redis(url: str) -> Redis:
    """Create an async Redis client for the given URL (e.g. ``redis://redis:6379/0``)."""
    return Redis.from_url(url, decode_responses=True)
