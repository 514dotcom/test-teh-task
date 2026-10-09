from __future__ import annotations

import asyncio
import logging

from src.common.logging import configure_logging
from src.infrastructure.config import settings
from src.infrastructure.database.outbox_publisher import publish_outbox_events
from src.infrastructure.message_broker.broker import broker
from src.interfaces.consumers.payment_consumer import payment_consumer  # noqa: F401

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON)
    logger.info("Starting payment consumer service")

    await broker.start()
    logger.info("Connected to RabbitMQ")

    outbox_task = asyncio.create_task(publish_outbox_events())

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down consumer service")
    finally:
        outbox_task.cancel()
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())