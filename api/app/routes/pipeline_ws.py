"""WebSocket pipeline status stream (US-21 D-59)."""

from __future__ import annotations

import asyncio
import secrets
import uuid

from aimpos_config import get_settings
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.domain.pipeline.status_read import build_pipeline_status_read
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.realtime.hub import PipelineHub

router = APIRouter(tags=["pipeline-realtime"])

_AUTH_TIMEOUT_SECONDS = 10.0
_MAX_CONNECTIONS = 10


def _verify_token(token: object) -> bool:
    if not isinstance(token, str) or not token:
        return False
    expected = get_settings().api_token
    return bool(expected) and secrets.compare_digest(token, expected)


@router.websocket("/ws/pipeline")
async def pipeline_websocket(websocket: WebSocket) -> None:
    hub: PipelineHub = websocket.app.state.pipeline_hub
    sessionmaker = websocket.app.state.sessionmaker

    await websocket.accept()
    await hub.register(websocket)

    try:
        try:
            first = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=_AUTH_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            await websocket.close(code=4401, reason="Unauthorized")
            return

        if first.get("type") != "auth" or not _verify_token(first.get("token")):
            await websocket.close(code=4401, reason="Unauthorized")
            return

        if await hub.connection_count_for_token() > _MAX_CONNECTIONS:
            await websocket.close(code=4408, reason="Too many connections")
            return

        await hub.mark_authenticated(websocket)
        await websocket.send_json({"type": "auth.ok"})

        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "pong":
                continue

            if msg_type != "subscribe":
                continue

            try:
                project_id = uuid.UUID(str(message["project_id"]))
            except (KeyError, ValueError):
                await websocket.close(code=4400, reason="Invalid subscribe")
                return

            async with sessionmaker() as session:
                if await ProjectRepository(session).get(project_id) is None:
                    await websocket.close(code=4404, reason="Project not found")
                    return
                run = await PipelineRunRepository(session).latest_for_project(project_id)
                snapshot = build_pipeline_status_read(project_id, run)

            await hub.subscribe(websocket, project_id)
            await websocket.send_json(
                {"type": "subscribed", "project_id": str(project_id)},
            )
            await websocket.send_json(
                {
                    "type": "pipeline.status",
                    "payload": snapshot.model_dump(mode="json"),
                },
            )

    except WebSocketDisconnect:
        pass
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
        await hub.remove(websocket)
