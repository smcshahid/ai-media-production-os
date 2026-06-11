#!/usr/bin/env python3
"""WebSocket smoke test for US-21 Olares verification (runs inside API pod)."""

from __future__ import annotations

import json
import os
import sys

try:
    from websocket import create_connection
except ImportError:
    print("FAIL missing websocket-client")
    sys.exit(1)


def main() -> int:
    token = os.environ["TOKEN"]
    project_id = os.environ["PROJECT_ID"]
    url = os.environ.get("WS_URL", "ws://127.0.0.1:8000/ws/pipeline")

    ws = create_connection(url, timeout=15)
    try:
        ws.send(json.dumps({"type": "auth", "token": token}))
        auth = json.loads(ws.recv())
        if auth.get("type") != "auth.ok":
            print("FAIL auth", auth)
            return 1

        ws.send(json.dumps({"type": "subscribe", "project_id": project_id}))
        sub = json.loads(ws.recv())
        if sub.get("type") != "subscribed":
            print("FAIL subscribe", sub)
            return 1

        event = json.loads(ws.recv())
        if event.get("type") != "pipeline.status":
            print("FAIL event", event)
            return 1

        print("WS_SMOKE=PASS status=", event["payload"].get("status"))
        return 0
    finally:
        ws.close()


if __name__ == "__main__":
    raise SystemExit(main())
