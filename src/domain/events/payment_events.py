from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class PaymentCreatedEvent:
    event_id: str
    payment_id: str
    money: Any
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    webhook_url: str = ""
    idempotency_key: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PaymentProcessingStartedEvent:
    event_id: str
    payment_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PaymentSucceededEvent:
    event_id: str
    payment_id: str
    money: Any = None
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PaymentFailedEvent:
    event_id: str
    payment_id: str
    reason: str = ""
    failed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))