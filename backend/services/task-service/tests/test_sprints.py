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
PROJECT_ID = "proj-001"
SPRINT_ID = str(ObjectId())


def _make_sprint(status="planned"):
    return {
        "_id": ObjectId(SPRINT_ID),
        "workspace_id": WORKSPACE_ID,
        "project_id": PROJECT_ID,
        "name": "Sprint 1",
        "goal": "Ship MVP",
        "status": status,
        "start_date": None,
        "end_date": None,
        "velocity": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


@pytest.mark.asyncio
async def test_create_sprint():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    sprint_doc = _make_sprint()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.delete = AsyncMock()

        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(SPRINT_ID)))
        mock_col.find_one = AsyncMock(return_value=sprint_doc)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/sprints/{WORKSPACE_ID}/{PROJECT_ID}",
                json={"name": "Sprint 1", "goal": "Ship MVP"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        assert response.json()["status"] == "planned"


@pytest.mark.asyncio
async def test_start_sprint():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    sprint_doc = _make_sprint(status="planned")
    updated = _make_sprint(status="active")

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.delete = AsyncMock()

        mock_sprints = AsyncMock()
        mock_sprints.find_one = AsyncMock(side_effect=[sprint_doc, updated])
        mock_sprints.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_sprints.count_documents = AsyncMock(return_value=0)

        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_sprints)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/sprints/{WORKSPACE_ID}/{PROJECT_ID}/{SPRINT_ID}/start",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_complete_sprint():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    sprint_doc = _make_sprint(status="active")
    updated = _make_sprint(status="completed")

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.delete = AsyncMock()

        mock_tasks = AsyncMock()
        mock_sprints = AsyncMock()
        mock_sprints.find_one = AsyncMock(side_effect=[sprint_doc, updated])
        mock_sprints.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_tasks.update_many = AsyncMock()

        def get_col(name):
            if name == "sprints":
                return mock_sprints
            return mock_tasks

        mock_db.return_value.__getitem__ = MagicMock(side_effect=get_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/sprints/{WORKSPACE_ID}/{PROJECT_ID}/{SPRINT_ID}/complete",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200
        mock_tasks.update_many.assert_called_once()


@pytest.mark.asyncio
async def test_cannot_start_already_active_sprint():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    sprint_doc = _make_sprint(status="planned")

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=sprint_doc)
        # Simulate another active sprint
        mock_col.count_documents = AsyncMock(return_value=1)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/sprints/{WORKSPACE_ID}/{PROJECT_ID}/{SPRINT_ID}/start",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 409
