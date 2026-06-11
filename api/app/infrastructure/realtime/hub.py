"""In-process WebSocket fan-out for pipeline status (US-21 D-59)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.domain.pipeline.status_read import PipelineStatusRead

logger = logging.getLogger("aimpos.realtime.hub")

_MAX_CONNECTIONS = 10


@dataclass
class _Connection:
    websocket: WebSocket
    authenticated: bool = False
    project_id: uuid.UUID | None = None


class PipelineHub:
    """Registry of authenticated WebSocket subscribers keyed by project_id."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: dict[WebSocket, _Connection] = {}
        self._by_project: dict[uuid.UUID, set[WebSocket]] = {}

    async def register(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[websocket] = _Connection(websocket=websocket)

    async def remove(self, websocket: WebSocket) -> None:
        async with self._lock:
            conn = self._connections.pop(websocket, None)
            if conn is None or conn.project_id is None:
                return
            project_set = self._by_project.get(conn.project_id)
            if project_set is not None:
                project_set.discard(websocket)
                if not project_set:
                    self._by_project.pop(conn.project_id, None)

    async def mark_authenticated(self, websocket: WebSocket) -> None:
        async with self._lock:
            conn = self._connections.get(websocket)
            if conn is not None:
                conn.authenticated = True

    async def connection_count_for_token(self) -> int:
        async with self._lock:
            return sum(1 for c in self._connections.values() if c.authenticated)

    async def subscribe(self, websocket: WebSocket, project_id: uuid.UUID) -> None:
        async with self._lock:
            conn = self._connections.get(websocket)
            if conn is None:
                return
            if conn.project_id is not None:
                old = self._by_project.get(conn.project_id)
                if old is not None:
                    old.discard(websocket)
            conn.project_id = project_id
            self._by_project.setdefault(project_id, set()).add(websocket)

    async def broadcast(self, project_id: uuid.UUID, payload: PipelineStatusRead) -> None:
        message = {
            "type": "pipeline.status",
            "payload": payload.model_dump(mode="json"),
        }
        async with self._lock:
            sockets = list(self._by_project.get(project_id, set()))

        dead: list[WebSocket] = []
        for websocket in sockets:
            try:
                if websocket.client_state != WebSocketState.CONNECTED:
                    dead.append(websocket)
                    continue
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead.append(websocket)

        for websocket in dead:
            await self.remove(websocket)

    async def send_ping(self) -> None:
        message = {"type": "ping"}
        async with self._lock:
            sockets = list(self._connections.keys())

        dead: list[WebSocket] = []
        for websocket in sockets:
            conn = self._connections.get(websocket)
            if conn is None or not conn.authenticated:
                continue
            try:
                if websocket.client_state != WebSocketState.CONNECTED:
                    dead.append(websocket)
                    continue
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead.append(websocket)

        for websocket in dead:
            await self.remove(websocket)

    async def start_heartbeat(self, interval_seconds: float = 30.0) -> asyncio.Task[None]:
        async def _loop() -> None:
            while True:
                await asyncio.sleep(interval_seconds)
                await self.send_ping()

        return asyncio.create_task(_loop())
