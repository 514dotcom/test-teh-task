from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from src.application.dtos.payment_dtos import CreatePaymentRequest, CreatePaymentResponse
from src.application.interfaces.repositories import (
    MessageBrokerPublisher,
    PaymentRepository,
    OutboxRepository,
    UnitOfWork,
)
from src.domain.entities.payment import Payment
from src.domain.events.payment_events import PaymentCreatedEvent
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money

logger = logging.getLogger(__name__)


class CreatePaymentUseCase:

    def __init__(
        self,
        payment_repo: PaymentRepository,
        outbox_repo: OutboxRepository,
        uow: UnitOfWork,
        publisher: MessageBrokerPublisher,
    ) -> None:
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo
        self._uow = uow
        self._publisher = publisher

    async def execute(
        self,
        request: CreatePaymentRequest,
        idempotency_key: str,
    ) -> CreatePaymentResponse:
        existing = await self._payment_repo.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            logger.info("Duplicate payment detected (idempotency key: %s)", idempotency_key)
            return CreatePaymentResponse(
                payment_id=existing.id,
                status=existing.status.value,
                created_at=existing.created_at,
            )

        money = Money(amount=Decimal(str(request.amount)), currency=Currency(request.currency))

        payment = Payment(
            id=Payment.generate_id(),
            money=money,
            description=request.description,
            metadata=request.metadata,
            webhook_url=str(request.webhook_url),
            idempotency_key=idempotency_key,
        )

        payment_id = payment.id
        event = PaymentCreatedEvent(
            event_id=str(uuid.uuid4()),
            payment_id=payment_id,
            money=money,
            description=request.description,
            metadata=request.metadata,
            webhook_url=str(request.webhook_url),
            idempotency_key=idempotency_key,
        )

        async with self._uow:
            await self._payment_repo.save(payment)
            await self._outbox_repo.save_event(
                event_id=event.event_id,
                event_type="payment.created",
                payload={
                    "payment_id": payment_id,
                    "amount": str(money.amount),
                    "currency": money.currency.value,
                    "description": request.description,
                    "metadata": request.metadata,
                    "webhook_url": str(request.webhook_url),
                    "idempotency_key": idempotency_key,
                },
            )
            await self._uow.commit()

        try:
            await self._publisher.publish(
                routing_key="payments.new",
                message={
                    "event_id": event.event_id,
                    "type": "payment.created",
                    "payment_id": payment_id,
                    "amount": str(money.amount),
                    "currency": money.currency.value,
                    "webhook_url": str(request.webhook_url),
                    "idempotency_key": idempotency_key,
                },
            )
            await self._outbox_repo.mark_as_published(event.event_id)
        except Exception:
            logger.warning(
                "Failed to publish event to broker, will rely on outbox polling (event_id: %s)",
                event.event_id,
            )

        logger.info("Payment created: %s (amount: %s %s)", payment_id, money.amount, money.currency.value)
        return CreatePaymentResponse(
            payment_id=payment_id,
            status=payment.status.value,
            created_at=payment.created_at,
        )