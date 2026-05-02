import sys
import os
import logging
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from redis_client import get_redis, CacheService

logger = logging.getLogger(__name__)

PRESENCE_TTL = 30  # seconds


class PresenceService:
    async def set_online(self, workspace_id: str, user_id: str) -> None:
        redis = await get_redis()
        cache = CacheService(redis)
        await cache.set_presence(workspace_id, user_id, "online")

    async def set_away(self, workspace_id: str, user_id: str) -> None:
        redis = await get_redis()
        cache = CacheService(redis)
        await cache.set_presence(workspace_id, user_id, "away")

    async def set_offline(self, workspace_id: str, user_id: str) -> None:
        redis = await get_redis()
        try:
            key = f"user_presence:{workspace_id}"
            await redis.hdel(key, user_id)
        except Exception as e:
            logger.error(f"Presence set_offline error: {e}")

    async def get_presence_map(self, workspace_id: str) -> dict[str, str]:
        redis = await get_redis()
        cache = CacheService(redis)
        try:
            return await cache.get_presence(workspace_id)
        except Exception as e:
            logger.error(f"Presence get error: {e}")
            return {}

    async def get_user_status(self, workspace_id: str, user_id: str) -> str:
        presence_map = await self.get_presence_map(workspace_id)
        return presence_map.get(user_id, "offline")

    async def heartbeat(self, workspace_id: str, user_id: str) -> None:
        """Extend TTL on user's presence entry (called on ping/activity)."""
        redis = await get_redis()
        try:
            key = f"user_presence:{workspace_id}"
            await redis.hset(key, user_id, "online")
            await redis.expire(key, PRESENCE_TTL)
        except Exception as e:
            logger.error(f"Presence heartbeat error: {e}")


presence_service = PresenceService()
