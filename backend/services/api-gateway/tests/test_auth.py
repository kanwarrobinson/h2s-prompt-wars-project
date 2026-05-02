import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


@pytest.fixture
def mock_firebase_token():
    return {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def mock_user_doc(mock_firebase_token):
    from datetime import datetime
    from bson import ObjectId
    return {
        "_id": ObjectId(),
        "firebase_uid": mock_firebase_token["uid"],
        "email": mock_firebase_token["email"],
        "display_name": "Test User",
        "avatar_url": None,
        "workspaces": [],
        "notification_prefs": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_login_with_valid_token(mock_firebase_token, mock_user_doc):
    app = make_app()
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=mock_firebase_token),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_user_doc)
        mock_collection.update_one = AsyncMock()
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)

        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.setex = AsyncMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"firebase_token": "valid.token.here"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == mock_firebase_token["email"]


@pytest.mark.asyncio
async def test_login_with_invalid_token():
    app = make_app()
    with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("Invalid token")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"firebase_token": "bad.token"},
            )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_without_auth():
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_auth(mock_firebase_token, mock_user_doc):
    app = make_app()
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=mock_firebase_token),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_user_doc)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid.token"},
            )

        assert response.status_code == 200
        assert response.json()["email"] == mock_firebase_token["email"]


@pytest.mark.asyncio
async def test_rate_limiting():
    """Rate limiter allows normal traffic but blocks excessive requests."""
    app = make_app()
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": "user1", "email": "u@test.com"}),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        # Simulate counter at limit
        mock_redis_inst.incr = AsyncMock(return_value=61)
        mock_redis_inst.expire = AsyncMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid.token"},
            )
        assert response.status_code == 429
