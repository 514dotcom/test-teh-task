# Payment Service

Асинхронный микросервис для процессинга платежей.

## Архитектура

4 слоя по DDD — детали реализации можно менять не трогая бизнес-логику:

- **Domain** — платеж, статусы, события. Ничего не знает про базу или rabbit.
- **Application** — сценарии использования: создать платеж, получить. Координирует домен и инфраструктуру.
- **Infrastructure** — база, брокер, вебхуки, аутентификация. Можно переписать под другую БД не трогая код выше.
- **Interfaces** — HTTP ручки и consumer для rabbit. Входные точки.

Главные фишки:
- **Outbox Pattern** — платеж и событие сохраняются в одной транзакции, фоновый процесс доставляет в rabbit. Событие не потеряется.
- **Idempotency-Key** — повторный запрос с тем же ключом вернет существующий платеж.
- **Dead Letter Queue** — после 3 неудачных попыток сообщение уходит в DLQ.
- **Экспоненциальный backoff** с джиттером на вебхуках и ретраях.

## Быстрый старт

```bash
docker compose up --build
```

API будет на `http://localhost:8000`.

Если без докера:

```bash
pip install -r requirements.txt
alembic upgrade head
# В одном терминале:
uvicorn src.interfaces.api.app:app --reload
# В другом:
python -m src.interfaces.consumers.main
```

## API

Все запросы с заголовком `X-API-Key: pay-secret-key-change-in-production`.

### Создать платеж

```http
POST /api/v1/payments
Idempotency-Key: my-unique-key-123
X-API-Key: pay-secret-key-change-in-production
Content-Type: application/json

{
    "amount": 100.50,
    "currency": "USD",
    "description": "Заказ #123",
    "metadata": {"order_id": "123"},
    "webhook_url": "https://example.com/webhook"
}
```

Ответ — `202 Accepted`:

```json
{
    "payment_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "created_at": "2026-10-05T12:00:00+00:00"
}
```

### Получить платеж

```http
GET /api/v1/payments/550e8400-e29b-41d4-a716-446655440000
X-API-Key: pay-secret-key-change-in-production
```

Ответ:

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": "100.50",
    "currency": "USD",
    "status": "succeeded",
    "created_at": "2026-10-05T12:00:00+00:00",
    "processed_at": "2026-10-05T12:00:03+00:00"
}
```

### Webhook

После обработки сервис дергает указанный URL с результатом:

```json
{
    "event": "payment.succeeded",
    "payment_id": "550e8400-...",
    "status": "succeeded",
    "processed_at": "2026-10-05T12:00:03+00:00"
}
```

## Переменные окружения

| Переменная | По умолчанию |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://payment:payment@postgres:5432/payment` |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` |
| `API_KEY` | `pay-secret-key-change-in-production` |