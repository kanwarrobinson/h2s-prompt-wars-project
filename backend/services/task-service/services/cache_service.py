import json
from typing import Any, Optional

import redis.asyncio as aioredis


class TaskCacheService:
    """Redis cache helper for task service operations."""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    def _sprint_board_key(self, workspace_id: str, sprint_id: str) -> str:
        return f"sprint_board:{workspace_id}:{sprint_id}"

    def _task_key(self, task_id: str) -> str:
        return f"task:{task_id}"

    def _tasks_list_key(self, workspace_id: str, filters: str = "") -> str:
        return f"tasks:{workspace_id}:{filters}"

    async def get_sprint_board(self, workspace_id: str, sprint_id: str) -> Optional[Any]:
        key = self._sprint_board_key(workspace_id, sprint_id)
        val = await self.redis.get(key)
        return json.loads(val) if val else None

    async def set_sprint_board(self, workspace_id: str, sprint_id: str, data: Any, ttl: int = 30) -> None:
        key = self._sprint_board_key(workspace_id, sprint_id)
        await self.redis.setex(key, ttl, json.dumps(data, default=str))

    async def invalidate_sprint_board(self, workspace_id: str, sprint_id: str) -> None:
        key = self._sprint_board_key(workspace_id, sprint_id)
        await self.redis.delete(key)

    async def get_task(self, task_id: str) -> Optional[Any]:
        key = self._task_key(task_id)
        val = await self.redis.get(key)
        return json.loads(val) if val else None

    async def set_task(self, task_id: str, data: Any, ttl: int = 120) -> None:
        key = self._task_key(task_id)
        await self.redis.setex(key, ttl, json.dumps(data, default=str))

    async def invalidate_task(self, task_id: str) -> None:
        await self.redis.delete(self._task_key(task_id))

    async def invalidate_workspace_tasks(self, workspace_id: str) -> None:
        """Delete all task list caches for a workspace."""
        pattern = f"tasks:{workspace_id}:*"
        keys = [key async for key in self.redis.scan_iter(pattern)]
        if keys:
            await self.redis.delete(*keys)
