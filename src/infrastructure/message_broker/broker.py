from __future__ import annotations

from faststream.rabbit import RabbitBroker

from src.infrastructure.config import settings

broker = RabbitBroker(
    url=settings.RABBITMQ_URL,
)


async def start_broker() -> None:
    await broker.start()


async def stop_broker() -> None:
    await broker.stop()