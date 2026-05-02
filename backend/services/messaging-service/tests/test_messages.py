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

MOCK_TOKEN = {"uid": "author-uid", "email": "author@example.com"}
CHANNEL_ID = str(ObjectId())
MSG_ID = str(ObjectId())
WORKSPACE_ID = "ws-001"


def _make_message(author_id="author-uid", deleted=False):
    return {
        "_id": ObjectId(MSG_ID),
        "channel_id": CHANNEL_ID,
        "workspace_id": WORKSPACE_ID,
        "author_id": author_id,
        "content": "Hello world",
        "thread_id": None,
        "reactions": {},
        "edited": False,
        "deleted": deleted,
        "reply_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def _make_channel():
    return {
        "_id": ObjectId(CHANNEL_ID),
        "workspace_id": WORKSPACE_ID,
        "name": "general",
        "type": "channel",
        "members": ["author-uid"],
        "is_private": False,
        "is_archived": False,
    }


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


@pytest.mark.asyncio
async def test_send_message():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    msg_doc = _make_message()
    channel_doc = _make_channel()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
        patch("pubsub_client.publish_event", new_callable=AsyncMock),
    ):
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(side_effect=[channel_doc, msg_doc])
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(MSG_ID)))
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/messages/{CHANNEL_ID}",
                json={"content": "Hello world"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        assert response.json()["content"] == "Hello world"


@pytest.mark.asyncio
async def test_message_pagination():
    from httpx import AsyncClient, ASGITransport
    app = make_app()

    messages = [
        {
            "_id": ObjectId(),
            "channel_id": CHANNEL_ID,
            "workspace_id": WORKSPACE_ID,
            "author_id": "author-uid",
            "content": f"Message {i}",
            "thread_id": None,
            "reactions": {},
            "edited": False,
            "deleted": False,
            "reply_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(50)
    ]

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__ = MagicMock(return_value=iter(messages))

        mock_col = AsyncMock()
        mock_col.find = MagicMock(return_value=mock_cursor)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/messages/{CHANNEL_ID}",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "has_more" in data


@pytest.mark.asyncio
async def test_add_and_toggle_reaction():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    msg_doc = _make_message()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        msg_after = dict(msg_doc)
        msg_after["reactions"] = {"👍": ["author-uid"]}

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=msg_doc)
        mock_col.update_one = AsyncMock()
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/messages/{CHANNEL_ID}/{MSG_ID}/reactions",
                json={"emoji": "👍"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        assert "users" in response.json()


@pytest.mark.asyncio
async def test_get_thread_replies():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    parent = _make_message()
    replies = [
        {**_make_message(), "_id": ObjectId(), "thread_id": MSG_ID, "content": f"Reply {i}"}
        for i in range(3)
    ]

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=MOCK_TOKEN),
        patch("db.get_db", new_callable=AsyncMock) as mock_db,
    ):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.__aiter__ = MagicMock(return_value=iter(replies))

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=parent)
        mock_col.find = MagicMock(return_value=mock_cursor)
        mock_db.return_value.__getitem__ = MagicMock(return_value=mock_col)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/messages/{CHANNEL_ID}/{MSG_ID}/thread",
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200
        assert "parent" in response.json()
        assert "replies" in response.json()
