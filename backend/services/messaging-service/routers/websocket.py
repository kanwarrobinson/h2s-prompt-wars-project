import sys
import os
import asyncio
import json
import logging
from typing import Dict, Set

import firebase_admin.auth as fb_auth
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from redis_client import get_redis, CacheService
from pubsub_client import publish_event

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # workspace_id -> set of websocket connections
        self._workspace_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id
        self._user_map: Dict[WebSocket, str] = {}

    async def connect(self, workspace_id: str, websocket: WebSocket, user_id: str) -> None:
        if workspace_id not in self._workspace_connections:
            self._workspace_connections[workspace_id] = set()
        self._workspace_connections[workspace_id].add(websocket)
        self._user_map[websocket] = user_id
        logger.info(f"User {user_id} connected to workspace {workspace_id}")

    def disconnect(self, workspace_id: str, websocket: WebSocket) -> None:
        if workspace_id in self._workspace_connections:
            self._workspace_connections[workspace_id].discard(websocket)
        user_id = self._user_map.pop(websocket, None)
        logger.info(f"User {user_id} disconnected from workspace {workspace_id}")

    async def broadcast_to_workspace(self, workspace_id: str, message: dict) -> None:
        connections = self._workspace_connections.get(workspace_id, set())
        if not connections:
            return
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in connections.copy():
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(workspace_id, ws)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        payload = json.dumps(message, default=str)
        for ws, uid in list(self._user_map.items()):
            if uid == user_id:
                try:
                    await ws.send_text(payload)
                except Exception:
                    pass


manager = ConnectionManager()


async def _pull_pubsub_messages(workspace_id: str) -> None:
    """Background task: pull Pub/Sub task events and broadcast to workspace."""
    pass


@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    await websocket.accept()

    authenticated_uid: str | None = None
    heartbeat_task: asyncio.Task | None = None

    try:
        # First message must be auth handshake
        auth_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_msg = json.loads(auth_raw)

        if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
            await websocket.send_text(json.dumps({"type": "error", "message": "Auth required"}))
            await websocket.close(code=4001)
            return

        try:
            decoded = fb_auth.verify_id_token(auth_msg["token"])
            authenticated_uid = decoded["uid"]
        except Exception:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid token"}))
            await websocket.close(code=4001)
            return

        await manager.connect(workspace_id, websocket, authenticated_uid)
        await websocket.send_text(json.dumps({"type": "auth_success", "user_id": authenticated_uid}))

        redis = await get_redis()
        cache = CacheService(redis)
        await cache.set_presence(workspace_id, authenticated_uid, "online")
        await manager.broadcast_to_workspace(
            workspace_id,
            {"type": "presence_update", "user_id": authenticated_uid, "status": "online"},
        )

        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    await cache.set_presence(workspace_id, authenticated_uid, "online")
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "pong":
                await cache.set_presence(workspace_id, authenticated_uid, "online")

            elif msg_type == "typing":
                await manager.broadcast_to_workspace(
                    workspace_id,
                    {
                        "type": "typing",
                        "user_id": authenticated_uid,
                        "channel_id": msg.get("channel_id"),
                    },
                )

            elif msg_type == "presence_update":
                status = msg.get("status", "online")
                await cache.set_presence(workspace_id, authenticated_uid, status)
                await manager.broadcast_to_workspace(
                    workspace_id,
                    {"type": "presence_update", "user_id": authenticated_uid, "status": status},
                )

            elif msg_type == "message":
                await manager.broadcast_to_workspace(
                    workspace_id,
                    {
                        "type": "message",
                        "channel_id": msg.get("channel_id"),
                        "author_id": authenticated_uid,
                        "content": msg.get("content"),
                    },
                )

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        await websocket.close(code=4002)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        if authenticated_uid:
            redis = await get_redis()
            cache = CacheService(redis)
            await cache.set_presence(workspace_id, authenticated_uid, "offline")
            manager.disconnect(workspace_id, websocket)
            await manager.broadcast_to_workspace(
                workspace_id,
                {"type": "presence_update", "user_id": authenticated_uid, "status": "offline"},
            )
