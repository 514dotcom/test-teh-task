from __future__ import annotations

import logging

from src.application.interfaces.repositories import PaymentRepository
from src.common.exceptions import PaymentNotFoundError
from src.domain.entities.payment import Payment

logger = logging.getLogger(__name__)


class GetPaymentUseCase:

    def __init__(self, payment_repo: PaymentRepository) -> None:
        self._payment_repo = payment_repo

    async def execute(self, payment_id: str) -> Payment:
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            logger.warning("Payment not found: %s", payment_id)
            raise PaymentNotFoundError(payment_id)
        return payment