import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


MOCK_TOKEN = {"uid": "owner-uid", "email": "owner@example.com"}
MOCK_WS_ID = str(ObjectId())


def _make_workspace(slug="test-ws"):
    return {
        "_id": ObjectId(MOCK_WS_ID),
        "name": "Test Workspace",
        "slug": slug,
        "description": "Test description",
        "github_org": None,
        "sso_enabled": False,
        "members": [{"user_id": "owner-uid", "role": "owner", "joined_at": datetime.utcnow()}],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_create_workspace():
    app = make_app()
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis.return_value = AsyncMock()

        ws_col = AsyncMock()
        users_col = AsyncMock()
        ws_col.find_one = AsyncMock(return_value=None)
        ws_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
        users_col.update_one = AsyncMock()

        def get_collection(name):
            return ws_col if name == "workspaces" else users_col

        mock_db.return_value.__getitem__ = MagicMock(side_effect=get_collection)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workspaces",
                json={"name": "My Workspace"},
                headers={"Authorization": "Bearer token"},
            )
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_workspace_as_member():
    app = make_app()
    ws = _make_workspace()
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.get = AsyncMock(return_value=None)
        mock_redis_inst.setex = AsyncMock()

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=ws)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/workspaces/{MOCK_WS_ID}",
                headers={"Authorization": "Bearer token"},
            )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Workspace"


@pytest.mark.asyncio
async def test_slug_uniqueness_on_create():
    app = make_app()
    existing = _make_workspace(slug="taken-slug")
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis.return_value = AsyncMock()
        ws_col = AsyncMock()
        ws_col.find_one = AsyncMock(return_value=existing)
        mock_db.return_value.__getitem__ = MagicMock(return_value=ws_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workspaces",
                json={"name": "Taken Slug", "slug": "taken-slug"},
                headers={"Authorization": "Bearer token"},
            )
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_non_member_cannot_access_workspace():
    app = make_app()
    ws = _make_workspace()
    other_token = {"uid": "stranger-uid", "email": "stranger@test.com"}
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=other_token),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_redis.return_value = AsyncMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=ws)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/workspaces/{MOCK_WS_ID}",
                headers={"Authorization": "Bearer token"},
            )
        assert response.status_code == 403
