from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from src.domain.entities.payment import Payment


class PaymentRepository(ABC):

    @abstractmethod
    async def save(self, payment: Payment) -> None: ...

    @abstractmethod
    async def get_by_id(self, payment_id: str) -> Payment | None: ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Payment | None: ...

    @abstractmethod
    async def update_status(self, payment: Payment) -> None: ...


class OutboxRepository(Protocol):

    async def save_event(self, event_id: str, event_type: str, payload: dict[str, Any]) -> None: ...

    async def get_pending_events(self, limit: int = 100) -> list[Any]: ...

    async def mark_as_published(self, event_id: str) -> None: ...

    async def delete_event(self, event_id: str) -> None: ...


class WebhookSender(Protocol):

    async def send(self, url: str, payload: dict[str, Any]) -> bool: ...


class MessageBrokerPublisher(Protocol):

    async def publish(self, routing_key: str, message: dict[str, Any]) -> None: ...


class UnitOfWork(Protocol):

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> "UnitOfWork": ...
    async def __aexit__(self, *args: Any) -> None: ...