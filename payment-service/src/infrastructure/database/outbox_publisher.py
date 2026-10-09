from __future__ import annotations

import asyncio
import logging

from src.infrastructure.config import settings
from src.infrastructure.database.repository import SQLAlchemyOutboxRepository
from src.infrastructure.database.session import create_engine, create_session_factory
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2.0
BATCH_SIZE = 50

engine = create_engine()
session_factory = create_session_factory(engine)


async def publish_outbox_events() -> None:
    while True:
        try:
            async with session_factory() as session:
                repo = SQLAlchemyOutboxRepository(session)
                events = await repo.get_pending_events(limit=BATCH_SIZE)

                for event in events:
                    try:
                        await broker.publish(
                            message=event.payload,
                            queue=settings.RABBITMQ_QUEUE_PAYMENTS_NEW,
                            routing_key=settings.RABBITMQ_QUEUE_PAYMENTS_NEW,
                        )
                        await repo.mark_as_published(event.event_id)
                        logger.debug("Outbox event %s published", event.event_id)
                    except Exception as e:
                        await repo.increment_retry(event.event_id, str(e))
                        logger.warning("Failed to publish outbox event %s: %s", event.event_id, e)

                await session.commit()

        except Exception as e:
            logger.exception("Outbox publisher error: %s", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)