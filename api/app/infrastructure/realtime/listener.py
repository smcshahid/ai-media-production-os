"""Redis pub/sub listener → WebSocket hub (US-21 D-59)."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.domain.pipeline.status_read import build_pipeline_status_read
from app.infrastructure.db.repositories.episode import EpisodeRepository
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.realtime.hub import PipelineHub

logger = logging.getLogger("aimpos.realtime.listener")

_CHANNEL_PATTERN = "aimpos:pipeline:*"


class PipelineRealtimeListener:
    def __init__(
        self,
        redis: Redis,
        sessionmaker: async_sessionmaker[Any],
        hub: PipelineHub,
    ) -> None:
        self._redis = redis
        self._sessionmaker = sessionmaker
        self._hub = hub
        self._task: asyncio.Task[None] | None = None

    def start(self) -> asyncio.Task[None]:
        self._task = asyncio.create_task(self._run())
        return self._task

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        backoff = 5.0
        while True:
            pubsub = self._redis.pubsub()
            try:
                await pubsub.psubscribe(_CHANNEL_PATTERN)
                logger.info("realtime.listener.subscribed", extra={"pattern": _CHANNEL_PATTERN})
                backoff = 5.0
                async for message in pubsub.listen():
                    if message["type"] != "pmessage":
                        continue
                    await self._handle_message(message["data"])
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    "realtime.listener.error",
                    extra={"error": str(exc), "retry_in": backoff},
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
            finally:
                try:
                    await pubsub.aclose()
                except Exception:
                    pass

    async def _handle_message(self, raw: bytes | str) -> None:
        try:
            data = json.loads(raw)
            project_id = uuid.UUID(str(data["project_id"]))
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.debug("realtime.listener.drop_malformed", extra={"error": str(exc)})
            return

        async with self._sessionmaker() as session:
            runs = PipelineRunRepository(session)
            run_id_raw = data.get("run_id")
            run = None
            if run_id_raw:
                try:
                    run = await runs.get(uuid.UUID(str(run_id_raw)))
                except ValueError:
                    run = None
            if run is None:
                run = await runs.latest_for_project(project_id)
            episode = None
            if run and run.episode_id:
                episode = await EpisodeRepository(session).get(run.episode_id)
            payload = build_pipeline_status_read(project_id, run, episode=episode)

        await self._hub.broadcast(project_id, payload)
