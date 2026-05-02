import json
import logging
from typing import Any
from .config import settings


async def publish_event(topic_id: str, event_type: str, data: dict) -> None:
    """Publish an event to a GCP Pub/Sub topic."""
    if settings.environment == "development":
        logging.info(f"[PubSub mock] {topic_id} {event_type}: {data}")
        return
    try:
        from google.cloud import pubsub_v1

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(settings.pubsub_project, topic_id)
        message = json.dumps(
            {"type": event_type, "data": data}, default=str
        ).encode("utf-8")
        future = publisher.publish(topic_path, message, event_type=event_type)
        future.result(timeout=10)
    except Exception as e:
        logging.error(f"Pub/Sub publish error: {e}")


async def publish_task_event(event_type: str, task: dict) -> None:
    await publish_event("devcollab-task-events", event_type, task)


async def publish_notification_event(event_type: str, payload: dict) -> None:
    await publish_event("devcollab-notification-events", event_type, payload)
