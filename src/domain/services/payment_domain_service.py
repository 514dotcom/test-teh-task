from __future__ import annotations

import asyncio
import random
from decimal import Decimal

from src.domain.entities.payment import Payment, PaymentStatus
from src.domain.value_objects.currency import Currency


class PaymentDomainService:
    SUCCESS_RATE = 0.9
    MIN_PROCESSING_SEC = 2.0
    MAX_PROCESSING_SEC = 5.0

    async def simulate_processing(self, payment: Payment) -> tuple[PaymentStatus, str | None]:
        delay = random.uniform(self.MIN_PROCESSING_SEC, self.MAX_PROCESSING_SEC)
        await asyncio.sleep(delay)

        if random.random() < self.SUCCESS_RATE:
            payment.mark_succeeded()
            return PaymentStatus.SUCCEEDED, None
        else:
            error_msg = random.choice([
                "Insufficient funds",
                "Card declined",
                "Gateway timeout",
                "Fraud detection triggered",
            ])
            payment.mark_failed(error_msg)
            return PaymentStatus.FAILED, error_msg

    @staticmethod
    def calculate_exponential_backoff(retry_count: int, base_delay: float = 1.0, max_delay: float = 30.0) -> float:
        delay = min(base_delay * (2 ** (retry_count - 1)), max_delay)
        jitter = random.uniform(-delay * 0.25, delay * 0.25)
        return max(0.1, delay + jitter)