import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from kombu.exceptions import OperationalError

from app.db import ensure_indexes
from app.logging import configure_logging
from app.repository import fail_credit, get_credit, ping, register_credit
from app.schemas import CreditAccepted, CreditRequest, CreditStatus
from app.tasks import process_credit

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    ensure_indexes()
    yield


app = FastAPI(lifespan=lifespan)


@app.post(
    "/credits",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CreditAccepted,
)
def create_credit(body: CreditRequest) -> CreditAccepted:
    task_id = str(uuid.uuid4())
    register_credit(task_id, body.user_id, body.amount)
    try:
        process_credit.apply_async(args=(task_id,))
    except OperationalError as exc:
        fail_credit(task_id, str(exc))
        logger.error(
            "event=publish_failed task_id=%s user_id=%s error=%s",
            task_id,
            body.user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="broker unavailable",
        ) from exc
    return CreditAccepted(task_id=task_id)


@app.get("/credits/{task_id}", response_model=CreditStatus)
def read_credit(task_id: str) -> CreditStatus:
    credit = get_credit(task_id)
    if credit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return CreditStatus(
        task_id=credit["_id"],
        user_id=credit["user_id"],
        amount=credit["amount"].to_decimal(),
        status=credit["status"],
    )


@app.get("/health")
def health() -> dict[str, str]:
    ping()
    return {"status": "ok"}
