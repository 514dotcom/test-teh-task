# Тестовое задание — Payment Service

Асинхронный микросервис для процессинга платежей на FastAPI + RabbitMQ + PostgreSQL.

## Состав

- `payment-service/` — исходный код микросервиса
  - FastAPI (HTTP API)
  - RabbitMQ consumer (обработка платежей)
  - Outbox pattern, idempotency, DLQ, webhooks

Подробнее — в [README сервиса](payment-service/README.md).