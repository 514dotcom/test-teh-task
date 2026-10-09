from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator

from src.domain.value_objects.currency import Currency


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl = Field(...)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        currency = v.upper()
        if currency not in {c.value for c in Currency}:
            raise ValueError(f"Unsupported currency: {v}. Supported: RUB, USD, EUR")
        return currency

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.01"):
            raise ValueError("Amount must be at least 0.01")
        return v.quantize(Decimal("0.01"))


class CreatePaymentResponse(BaseModel):
    id: str = Field(..., alias="payment_id")
    status: str
    created_at: datetime

    model_config = {"populate_by_name": True}


class PaymentResponse(BaseModel):
    id: str
    amount: str
    currency: str
    description: str
    metadata: dict[str, Any]
    webhook_url: str
    idempotency_key: str
    status: str
    created_at: datetime
    processed_at: datetime | None = None
    retry_count: int = 0
    last_error: str | None = None