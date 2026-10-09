from __future__ import annotations

from typing import Any


class DomainError(Exception):
    pass


class PaymentNotFoundError(DomainError):
    def __init__(self, payment_id: str) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment with id '{payment_id}' not found")


class DuplicatePaymentError(DomainError):
    def __init__(self, idempotency_key: str) -> None:
        self.idempotency_key = idempotency_key
        super().__init__(f"Payment with idempotency key '{idempotency_key}' already exists")


class InvalidPaymentAmountError(DomainError):
    def __init__(self, amount: Any) -> None:
        self.amount = amount
        super().__init__(f"Invalid payment amount: {amount}")


class InvalidCurrencyError(DomainError):
    def __init__(self, currency: str) -> None:
        self.currency = currency
        super().__init__(f"Invalid currency: {currency}. Supported: RUB, USD, EUR")


class WebhookDeliveryError(DomainError):
    def __init__(self, payment_id: str, webhook_url: str, status_code: int | None = None) -> None:
        self.payment_id = payment_id
        self.webhook_url = webhook_url
        self.status_code = status_code
        msg = f"Failed to deliver webhook for payment '{payment_id}' to {webhook_url}"
        if status_code is not None:
            msg += f" (HTTP {status_code})"
        super().__init__(msg)


class PaymentProcessingError(DomainError):
    def __init__(self, payment_id: str, reason: str) -> None:
        self.payment_id = payment_id
        self.reason = reason
        super().__init__(f"Payment '{payment_id}' processing failed: {reason}")


class AuthenticationError(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid or missing API key")