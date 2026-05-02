from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

_client: AsyncIOMotorClient | None = None


async def get_db() -> AsyncIOMotorDatabase:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
        )
    return _client["devcollab"]


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


async def init_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create all required MongoDB indexes."""
    await db["tasks"].create_index([("workspace_id", 1), ("status", 1)])
    await db["tasks"].create_index([("workspace_id", 1), ("sprint_id", 1)])
    await db["tasks"].create_index([("workspace_id", 1), ("assignee_ids", 1)])
    await db["tasks"].create_index([("workspace_id", 1), ("updated_at", -1)])
    await db["messages"].create_index([("channel_id", 1), ("created_at", -1)])
    await db["messages"].create_index([("workspace_id", 1), ("author_id", 1)])
    await db["activity_logs"].create_index([("workspace_id", 1), ("created_at", -1)])
    await db["activity_logs"].create_index([("entity_id", 1)])
    await db["workspaces"].create_index([("slug", 1)], unique=True)
    await db["users"].create_index([("firebase_uid", 1)], unique=True)
    await db["users"].create_index([("email", 1)])
