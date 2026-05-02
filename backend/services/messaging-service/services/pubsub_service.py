import sys
import os
import asyncio
import json
import logging
from typing import Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from config import settings

logger = logging.getLogger(__name__)


class PubSubService:
    """Subscribe to Pub/Sub topics and route messages to handlers."""

    def __init__(self, project_id: str, subscription_id: str):
        self.project_id = project_id
        self.subscription_id = subscription_id
        self._handlers: dict[str, list[Callable]] = {}
        self._running = False

    def register_handler(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def start(self) -> None:
        if settings.environment == "development":
            logger.info(f"[PubSub mock] Not starting subscriber in development mode")
            return

        self._running = True
        asyncio.create_task(self._pull_loop())

    async def stop(self) -> None:
        self._running = False

    async def _pull_loop(self) -> None:
        try:
            from google.cloud import pubsub_v1

            subscriber = pubsub_v1.SubscriberClient()
            subscription_path = subscriber.subscription_path(
                self.project_id, self.subscription_id
            )

            def _callback(message):
                try:
                    data = json.loads(message.data.decode("utf-8"))
                    event_type = data.get("type", "unknown")
                    handlers = self._handlers.get(event_type, []) + self._handlers.get("*", [])
                    for handler in handlers:
                        asyncio.create_task(handler(data))
                    message.ack()
                except Exception as e:
                    logger.error(f"PubSub message handling error: {e}")
                    message.nack()

            streaming_pull_future = subscriber.subscribe(subscription_path, callback=_callback)
            logger.info(f"Listening for messages on {subscription_path}")

            while self._running:
                await asyncio.sleep(1)

            streaming_pull_future.cancel()
        except Exception as e:
            logger.error(f"PubSub subscriber error: {e}")
