import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

MOCK_TOKEN = {"uid": "user-abc", "email": "user@example.com"}
WORKSPACE_ID = "ws-001"
CHANNEL_ID = str(ObjectId())


def _make_channel(channel_type="channel"):
    return {
        "_id": ObjectId(CHANNEL_ID),
        "workspace_id": WORKSPACE_ID,
        "name": "general",
        "description": "General discussion",
        "type": channel_type,
        "is_private": False,
        "members": ["user-abc"],
        "created_by": "user-abc",
        "is_archived": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


@pytest.mark.asyncio
async def test_create_channel():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    channel_doc = _make_channel()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(side_effect=[None, channel_doc])
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(CHANNEL_ID)))
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/channels/{WORKSPACE_ID}",
                json={"name": "general"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        assert response.json()["name"] == "general"


@pytest.mark.asyncio
async def test_create_dm_channel():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    dm_doc = _make_channel(channel_type="dm")
    dm_doc["type"] = "dm"
    dm_doc["members"] = ["user-abc", "user-xyz"]

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(side_effect=[None, dm_doc])
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(CHANNEL_ID)))
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/channels/dm",
                json={"workspace_id": WORKSPACE_ID, "target_user_id": "user-xyz"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        assert response.json()["type"] == "dm"


@pytest.mark.asyncio
async def test_duplicate_dm_returns_existing():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    existing_dm = _make_channel(channel_type="dm")
    existing_dm["type"] = "dm"
    existing_dm["members"] = ["user-abc", "user-xyz"]

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=existing_dm)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/channels/dm",
                json={"workspace_id": WORKSPACE_ID, "target_user_id": "user-xyz"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        assert response.json()["type"] == "dm"
