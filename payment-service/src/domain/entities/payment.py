from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from src.domain.value_objects.money import Money


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Payment:
    id: str
    money: Money
    description: str
    metadata: dict[str, Any]
    webhook_url: str
    idempotency_key: str
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = None
    retry_count: int = 0
    last_error: str | None = None

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    def mark_succeeded(self) -> None:
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot mark {self.status} payment as succeeded")
        self.status = PaymentStatus.SUCCEEDED
        self.processed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot mark {self.status} payment as failed")
        self.status = PaymentStatus.FAILED
        self.processed_at = datetime.now(timezone.utc)
        self.last_error = error

    def increment_retry(self) -> int:
        self.retry_count += 1
        return self.retry_count

    @property
    def is_finalized(self) -> bool:
        return self.status in (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "amount": str(self.money.amount),
            "currency": self.money.currency.value,
            "description": self.description,
            "metadata": self.metadata,
            "webhook_url": self.webhook_url,
            "idempotency_key": self.idempotency_key,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
        }