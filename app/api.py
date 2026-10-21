from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.db import client, ensure_indexes
from app.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    ensure_indexes()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    client.admin.command("ping")
    return {"status": "ok"}
