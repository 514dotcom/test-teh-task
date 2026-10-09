from __future__ import annotations

import logging
from typing import Any

import httpx

from src.infrastructure.config import settings

logger = logging.getLogger(__name__)


class HttpxWebhookSender:

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=settings.WEBHOOK_TIMEOUT_SECONDS,
            limits=httpx.Limits(max_connections=50),
        )

    async def send(self, url: str, payload: dict[str, Any]) -> bool:
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook delivered to %s (status: %s)", url, response.status_code)
            return True
        except httpx.HTTPStatusError as e:
            logger.warning("Webhook HTTP error to %s: %s", url, e.response.status_code)
            return False
        except httpx.RequestError as e:
            logger.warning("Webhook request error to %s: %s", url, str(e))
            return False

    async def close(self) -> None:
        await self._client.aclose()