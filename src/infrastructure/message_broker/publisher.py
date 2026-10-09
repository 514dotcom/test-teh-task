from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


class FastStreamPublisher:

    async def publish(self, routing_key: str, message: dict[str, Any]) -> None:
        await broker.publish(
            message=message,
            queue=routing_key,
            routing_key=routing_key,
        )
        logger.debug("Published message to %s: %s", routing_key, message.get("event_id"))