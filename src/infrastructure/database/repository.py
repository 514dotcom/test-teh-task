from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import PaymentRepository
from src.domain.entities.payment import Payment, PaymentStatus
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.infrastructure.database.models.outbox import OutboxEventModel
from src.infrastructure.database.models.payment import PaymentModel

logger = logging.getLogger(__name__)


class SQLAlchemyPaymentRepository(PaymentRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, payment: Payment) -> None:
        model = self._to_model(payment)
        self._session.add(model)

    async def get_by_id(self, payment_id: str) -> Payment | None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.idempotency_key == key)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update_status(self, payment: Payment) -> None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.id == payment.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            logger.error("Cannot update status: Payment %s not found in DB", payment.id)
            return

        model.status = payment.status.value
        model.processed_at = payment.processed_at
        model.retry_count = payment.retry_count
        model.last_error = payment.last_error

    @staticmethod
    def _to_model(payment: Payment) -> PaymentModel:
        return PaymentModel(
            id=payment.id,
            amount=payment.money.amount,
            currency=payment.money.currency.value,
            description=payment.description,
            extra_data=payment.metadata,
            webhook_url=payment.webhook_url,
            idempotency_key=payment.idempotency_key,
            status=payment.status.value,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
            retry_count=payment.retry_count,
            last_error=payment.last_error,
        )

    @staticmethod
    def _to_domain(model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            money=Money(amount=model.amount, currency=Currency(model.currency)),
            description=model.description,
            metadata=model.extra_data,
            webhook_url=model.webhook_url,
            idempotency_key=model.idempotency_key,
            status=PaymentStatus(model.status),
            created_at=model.created_at,
            processed_at=model.processed_at,
            retry_count=model.retry_count,
            last_error=model.last_error,
        )


class SQLAlchemyOutboxRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_event(self, event_id: str, event_type: str, payload: dict[str, Any]) -> None:
        model = OutboxEventModel(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            is_published=False,
        )
        self._session.add(model)

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEventModel]:
        result = await self._session.execute(
            select(OutboxEventModel)
            .where(OutboxEventModel.is_published == False)  # noqa: E712
            .order_by(OutboxEventModel.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_as_published(self, event_id: str) -> None:
        from datetime import datetime, timezone

        await self._session.execute(
            text(
                "UPDATE outbox SET is_published = true, published_at = :now "
                "WHERE event_id = :event_id"
            ).bindparams(
                event_id=event_id,
                now=datetime.now(timezone.utc),
            )
        )

    async def delete_event(self, event_id: str) -> None:
        await self._session.execute(
            text("DELETE FROM outbox WHERE event_id = :event_id").bindparams(event_id=event_id)
        )

    async def increment_retry(self, event_id: str, error: str) -> None:
        await self._session.execute(
            text(
                "UPDATE outbox SET retry_count = retry_count + 1, last_error = :error "
                "WHERE event_id = :event_id"
            ).bindparams(event_id=event_id, error=error)
        )