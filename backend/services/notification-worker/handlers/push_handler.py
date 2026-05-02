import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


async def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """Send an FCM push notification via Firebase Admin SDK."""
    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="notification_icon",
                    color="#4f46e5",
                    click_action="OPEN_ACTIVITY",
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(title=title, body=body),
                        badge=1,
                        sound="default",
                    )
                )
            ),
        )
        response = messaging.send(message)
        logger.info(f"FCM push sent: {response}")
        return True
    except Exception as e:
        logger.error(f"FCM push error: {e}")
        return False


async def handle_push_notification(payload: dict) -> bool:
    """Handle a push notification job from Cloud Tasks."""
    fcm_token = payload.get("fcm_token")
    if not fcm_token:
        logger.warning("Push notification missing FCM token")
        return False

    notification_type = payload.get("type", "general")
    workspace_name = payload.get("workspace_name", "DevCollab")

    titles = {
        "task_assigned": "Task Assigned",
        "mention": "You Were Mentioned",
        "message": f"New message in {payload.get('channel_name', 'a channel')}",
        "sprint_started": "Sprint Started",
        "sprint_completed": "Sprint Completed",
        "general": "DevCollab Notification",
    }

    bodies = {
        "task_assigned": f"{payload.get('assigned_by', 'Someone')} assigned you: {payload.get('task_title', 'a task')}",
        "mention": f"{payload.get('mentioned_by', 'Someone')} mentioned you",
        "message": payload.get("message_preview", "You have a new message"),
        "sprint_started": f"Sprint '{payload.get('sprint_name', '')}' has started",
        "sprint_completed": f"Sprint '{payload.get('sprint_name', '')}' has been completed",
        "general": payload.get("message", "You have a new notification"),
    }

    title = f"[{workspace_name}] {titles.get(notification_type, 'Notification')}"
    body = bodies.get(notification_type, "You have a new notification")

    return await send_push_notification(
        fcm_token,
        title,
        body,
        data={
            "type": notification_type,
            "workspace_id": str(payload.get("workspace_id", "")),
            "url": payload.get("url", "/"),
        },
    )
