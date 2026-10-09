from __future__ import annotations

from enum import StrEnum


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"

    @classmethod
    def _missing_(cls, value: str) -> Currency | None:
        for member in cls:
            if member.value.upper() == value.upper():
                return member
        return None

    @classmethod
    def is_supported(cls, value: str) -> bool:
        return value.upper() in {c.value for c in cls}