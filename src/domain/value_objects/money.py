from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from src.common.exceptions import InvalidPaymentAmountError
from src.domain.value_objects.currency import Currency


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount < Decimal("0.01"):
            raise InvalidPaymentAmountError(self.amount)
        object.__setattr__(self, "amount", self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __repr__(self) -> str:
        return f"{self.amount:.2f} {self.currency.value}"

    @classmethod
    def from_decimal(cls, amount: Decimal | str | float | int, currency: str | Currency) -> Money:
        if isinstance(currency, str):
            currency = Currency(currency.upper())
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        return cls(amount=amount, currency=currency)

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency.value,
        }