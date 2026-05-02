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
TASK_ID = str(ObjectId())


def _make_task_doc(status="todo"):
    return {
        "_id": ObjectId(TASK_ID),
        "workspace_id": WORKSPACE_ID,
        "project_id": None,
        "sprint_id": None,
        "title": "Fix login bug",
        "description": "Users can't log in",
        "type": "bug",
        "status": status,
        "priority": "high",
        "assignee_ids": [],
        "reporter_id": "user-abc",
        "labels": ["auth"],
        "story_points": 3,
        "due_date": None,
        "github_pr_urls": [],
        "comments": [],
        "attachments": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


@pytest.mark.asyncio
async def test_list_tasks_cache_miss():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    task_doc = _make_task_doc()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.get = AsyncMock(return_value=None)
        mock_redis_inst.setex = AsyncMock()

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__ = AsyncMock(return_value=iter([task_doc]))

        mock_col = AsyncMock()
        mock_col.find = MagicMock(return_value=mock_cursor)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/tasks/{WORKSPACE_ID}",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_tasks_cache_hit():
    from httpx import AsyncClient, ASGITransport
    import json
    app = make_app()
    cached_tasks = [{"id": TASK_ID, "title": "Cached task", "status": "todo"}]

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.get = AsyncMock(return_value=json.dumps(cached_tasks))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/tasks/{WORKSPACE_ID}",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200
        assert response.json()[0]["title"] == "Cached task"


@pytest.mark.asyncio
async def test_create_task():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    task_doc = _make_task_doc()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
        patch("pubsub_client.publish_task_event", new_callable=AsyncMock),
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.scan_iter = MagicMock(return_value=aiter([]))
        mock_redis_inst.delete = AsyncMock()

        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(TASK_ID)))
        mock_col.find_one = AsyncMock(return_value=task_doc)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/tasks/{WORKSPACE_ID}",
                json={
                    "workspace_id": WORKSPACE_ID,
                    "title": "Fix login bug",
                    "type": "bug",
                    "priority": "high",
                },
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201


async def aiter(iterable):
    for item in iterable:
        yield item


@pytest.mark.asyncio
async def test_update_task_cache_invalidation():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    task_doc = _make_task_doc(status="in_progress")

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("redis_client.get_redis", new_callable=AsyncMock) as mock_redis,
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
        patch("pubsub_client.publish_task_event", new_callable=AsyncMock),
        patch("firestore_client.sync_task_to_firestore", new_callable=AsyncMock),
    ):
        mock_redis_inst = AsyncMock()
        mock_redis.return_value = mock_redis_inst
        mock_redis_inst.delete = AsyncMock()
        mock_redis_inst.scan_iter = MagicMock(return_value=aiter([f"tasks:{WORKSPACE_ID}::"]))

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(side_effect=[task_doc, task_doc])
        mock_col.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/tasks/{WORKSPACE_ID}/{TASK_ID}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200
        mock_redis_inst.delete.assert_called()
