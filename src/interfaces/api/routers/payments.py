from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.payment_dtos import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentResponse,
)
from src.application.use_cases.create_payment import CreatePaymentUseCase
from src.application.use_cases.get_payment import GetPaymentUseCase
from src.common.exceptions import PaymentNotFoundError
from src.infrastructure.auth.api_key_auth import verify_api_key
from src.infrastructure.database.repository import (
    SQLAlchemyOutboxRepository,
    SQLAlchemyPaymentRepository,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.message_broker.publisher import FastStreamPublisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=CreatePaymentResponse)
async def create_payment(
    body: CreatePaymentRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    _: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session),
) -> CreatePaymentResponse:
    payment_repo = SQLAlchemyPaymentRepository(session)
    outbox_repo = SQLAlchemyOutboxRepository(session)
    uow = SQLAlchemyUnitOfWork(session)
    publisher = FastStreamPublisher()

    use_case = CreatePaymentUseCase(
        payment_repo=payment_repo,
        outbox_repo=outbox_repo,
        uow=uow,
        publisher=publisher,
    )

    return await use_case.execute(body, idempotency_key)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str = Path(..., description="Payment ID"),
    _: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session),
) -> PaymentResponse:
    payment_repo = SQLAlchemyPaymentRepository(session)
    use_case = GetPaymentUseCase(payment_repo=payment_repo)

    try:
        payment = await use_case.execute(payment_id)
        return PaymentResponse(**payment.to_dict())
    except PaymentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with id '{payment_id}' not found",
        )