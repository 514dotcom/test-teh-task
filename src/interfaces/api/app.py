from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.common.exceptions import AuthenticationError, DomainError
from src.common.logging import configure_logging
from src.infrastructure.config import settings
from src.infrastructure.message_broker.broker import start_broker, stop_broker
from src.interfaces.api.middleware import RequestIDMiddleware
from src.interfaces.api.routers.payments import router as payments_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON)
    await start_broker()
    yield
    await stop_broker()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)

app.include_router(payments_router)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_code": exc.__class__.__name__},
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.APP_NAME}