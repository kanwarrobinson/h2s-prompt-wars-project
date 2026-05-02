import os
import pytest
from unittest.mock import AsyncMock, patch


os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")


def make_app():
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"):
        from main import app
        return app


@pytest.mark.asyncio
async def test_email_handler_mock():
    """Email handler returns True in development (mock mode, no API key)."""
    from handlers.email_handler import send_email
    result = await send_email(
        "test@example.com",
        "Test User",
        "Test subject",
        "<p>Hello</p>",
    )
    assert result is True


@pytest.mark.asyncio
async def test_handle_email_notification():
    """handle_email_notification sends the correct template."""
    from handlers.email_handler import handle_email_notification
    payload = {
        "type": "task_assigned",
        "email": "user@example.com",
        "name": "Test User",
        "workspace_name": "Acme Corp",
        "task_title": "Fix login bug",
        "assigned_by": "Alice",
        "task_url": "https://app.devcollab.com/tasks/123",
    }
    result = await handle_email_notification(payload)
    assert result is True


@pytest.mark.asyncio
async def test_push_handler_missing_token():
    """Push handler returns False when FCM token is missing."""
    from handlers.push_handler import handle_push_notification
    result = await handle_push_notification({"type": "mention"})
    assert result is False


@pytest.mark.asyncio
async def test_digest_handler_empty():
    """Digest handler returns True even with no items (skips gracefully)."""
    from handlers.digest_handler import handle_digest
    result = await handle_digest({
        "user_id": "user-123",
        "email": "user@example.com",
        "name": "Test User",
        "workspace_id": "ws-001",
        "workspace_name": "Acme Corp",
        "period": "daily",
    })
    assert result is True


@pytest.mark.asyncio
async def test_email_task_endpoint():
    from httpx import AsyncClient, ASGITransport
    app = make_app()
    with patch("handlers.email_handler.send_email", new_callable=AsyncMock, return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tasks/email",
                json={
                    "job_type": "email",
                    "payload": {
                        "type": "general",
                        "email": "user@example.com",
                        "name": "Test",
                        "subject": "Hello",
                        "html_content": "<p>Hello</p>",
                    },
                },
            )
        assert response.status_code == 200
        assert response.json()["status"] == "sent"
