import json
from typing import Any, Optional
import redis.asyncio as aioredis
from .config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


class CacheService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def get_json(self, key: str) -> Optional[Any]:
        val = await self.redis.get(key)
        return json.loads(val) if val else None

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        await self.redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, *keys: str) -> None:
        if keys:
            await self.redis.delete(*keys)

    async def set_presence(self, workspace_id: str, user_id: str, status: str) -> None:
        key = f"user_presence:{workspace_id}"
        await self.redis.hset(key, user_id, status)
        await self.redis.expire(key, 30)

    async def get_presence(self, workspace_id: str) -> dict:
        key = f"user_presence:{workspace_id}"
        return await self.redis.hgetall(key)

    async def check_rate_limit(self, user_id: str, endpoint: str, limit: int = 60) -> bool:
        key = f"rate:{user_id}:{endpoint}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)
        return count <= limit
