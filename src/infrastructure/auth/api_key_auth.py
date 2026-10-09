from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from src.infrastructure.config import settings

API_KEY_HEADER = "X-API-Key"


async def verify_api_key(x_api_key: Annotated[str, Header()] = "") -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if not secrets.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return x_api_key