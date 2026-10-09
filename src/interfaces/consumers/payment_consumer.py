from __future__ import annotations

import asyncio
import logging
from typing import Any

from faststream.rabbit import RabbitQueue

from src.domain.entities.payment import PaymentStatus
from src.domain.services.payment_domain_service import PaymentDomainService
from src.infrastructure.config import settings
from src.infrastructure.database.repository import SQLAlchemyPaymentRepository
from src.infrastructure.database.session import create_engine, create_session_factory
from src.infrastructure.message_broker.broker import broker
from src.infrastructure.webhooks.sender import HttpxWebhookSender

logger = logging.getLogger(__name__)

MAX_RETRIES = settings.RABBITMQ_MAX_RETRIES
DLQ_QUEUE = settings.RABBITMQ_QUEUE_PAYMENTS_DLQ
WEBHOOK_MAX_RETRIES = settings.WEBHOOK_MAX_RETRIES

engine = create_engine()
session_factory = create_session_factory(engine)
domain_service = PaymentDomainService()


async def _send_webhook_with_retry(
    sender: HttpxWebhookSender,
    url: str,
    payload: dict[str, Any],
    payment_id: str,
) -> bool:
    for attempt in range(1, WEBHOOK_MAX_RETRIES + 1):
        success = await sender.send(url, payload)
        if success:
            return True

        if attempt < WEBHOOK_MAX_RETRIES:
            delay = PaymentDomainService.calculate_exponential_backoff(attempt)
            logger.warning(
                "Webhook retry %d/%d for payment %s in %.1fs",
                attempt, WEBHOOK_MAX_RETRIES, payment_id, delay,
            )
            await asyncio.sleep(delay)

    logger.error("Webhook failed after %d attempts for payment %s", WEBHOOK_MAX_RETRIES, payment_id)
    return False


async def process_payment(message: dict[str, Any]) -> None:
    payment_id = message.get("payment_id", "")
    event_id = message.get("event_id", "")
    webhook_url = message.get("webhook_url", "")
    amount = message.get("amount", "0")
    currency_str = message.get("currency", "RUB")

    logger.info("Processing payment %s (event: %s)", payment_id, event_id)

    async with session_factory() as session:
        try:
            payment_repo = SQLAlchemyPaymentRepository(session)

            payment = await payment_repo.get_by_id(payment_id)
            if payment is None:
                logger.error("Payment %s not found in database", payment_id)
                return

            if payment.is_finalized:
                logger.info("Payment %s already finalized (status: %s)", payment_id, payment.status)
                return

            status, error = await domain_service.simulate_processing(payment)
            await payment_repo.update_status(payment)
            await session.commit()

            sender = HttpxWebhookSender()

            if status == PaymentStatus.SUCCEEDED:
                webhook_payload = {
                    "event": "payment.succeeded",
                    "payment_id": payment_id,
                    "amount": amount,
                    "currency": currency_str,
                    "status": "succeeded",
                    "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
                }
            else:
                webhook_payload = {
                    "event": "payment.failed",
                    "payment_id": payment_id,
                    "amount": amount,
                    "currency": currency_str,
                    "status": "failed",
                    "error": error,
                    "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
                }

            await _send_webhook_with_retry(sender, webhook_url, webhook_payload, payment_id)
            await sender.close()

            logger.info("Payment %s processed: %s", payment_id, status.value)

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to process payment %s: %s", payment_id, str(e))
            raise


@broker.subscriber(
    queue=RabbitQueue(
        name=settings.RABBITMQ_QUEUE_PAYMENTS_NEW,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": DLQ_QUEUE,
        },
    ),
)
async def payment_consumer(message: dict[str, Any]) -> None:
    await _process_with_dlq_protection(message)


async def _process_with_dlq_protection(message: dict[str, Any]) -> None:
    retry_count = message.get("x-retry-count", 0)

    if retry_count >= MAX_RETRIES:
        logger.error(
            "Payment %s exceeded max retries (%d), sending to DLQ",
            message.get("payment_id"), MAX_RETRIES,
        )
        await broker.publish(
            message=message,
            queue=DLQ_QUEUE,
            routing_key=DLQ_QUEUE,
        )
        return

    message["x-retry-count"] = retry_count + 1
    await process_payment(message)