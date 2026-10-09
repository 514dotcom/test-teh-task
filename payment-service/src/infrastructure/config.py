from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_file_optional=True,
        case_sensitive=False,
    )

    APP_NAME: str = "payment-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://payment:payment@localhost:5432/payment"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_QUEUE_PAYMENTS_NEW: str = "payments.new"
    RABBITMQ_QUEUE_PAYMENTS_DLQ: str = "payments.dlq"
    RABBITMQ_EXCHANGE_PAYMENTS: str = "payments"
    RABBITMQ_MAX_RETRIES: int = 3

    API_KEY: str = "pay-secret-key-change-in-production"

    WEBHOOK_TIMEOUT_SECONDS: int = 10
    WEBHOOK_MAX_RETRIES: int = 3

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1


settings = Settings()  # type: ignore[call-arg]