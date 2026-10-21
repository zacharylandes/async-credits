from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from bson.decimal128 import Decimal128
from pymongo.client_session import ClientSession

from app.db import client, credits_collection, users_collection


def register_credit(task_id: str, user_id: str, amount: Decimal) -> None:
    def txn(session: ClientSession) -> None:
        credits_collection.insert_one(
            {
                "_id": task_id,
                "user_id": user_id,
                "amount": Decimal128(str(amount)),
                "status": "pending",
                "created_at": datetime.now(UTC),
                "processed_at": None,
                "error": None,
            },
            session=session,
        )
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {"pending_count": 1},
                "$set": {"status": "processing"},
                "$setOnInsert": {"user_id": user_id},
            },
            upsert=True,
            session=session,
        )

    with client.start_session() as session:
        session.with_transaction(txn)


def apply_credit(task_id: str) -> bool:
    def txn(session: ClientSession) -> bool:
        # Claim is the idempotency gate: only one caller can move pending → processed.
        claimed = credits_collection.find_one_and_update(
            {"_id": task_id, "status": "pending"},
            {
                "$set": {
                    "status": "processed",
                    "processed_at": datetime.now(UTC),
                }
            },
            session=session,
        )
        if claimed is None:
            return False
        users_collection.update_one(
            {"user_id": claimed["user_id"]},
            {"$inc": {"balance": claimed["amount"], "pending_count": -1}},
            upsert=True,
            session=session,
        )
        settle_status(claimed["user_id"], session)
        return True

    with client.start_session() as session:
        return session.with_transaction(txn)


def fail_credit(task_id: str, error: str) -> bool:
    def txn(session: ClientSession) -> bool:
        claimed = credits_collection.find_one_and_update(
            {"_id": task_id, "status": "pending"},
            {
                "$set": {
                    "status": "failed",
                    "processed_at": datetime.now(UTC),
                    "error": error,
                }
            },
            session=session,
        )
        if claimed is None:
            return False
        users_collection.update_one(
            {"user_id": claimed["user_id"]},
            {"$inc": {"pending_count": -1}},
            session=session,
        )
        settle_status(claimed["user_id"], session)
        return True

    with client.start_session() as session:
        return session.with_transaction(txn)


def settle_status(user_id: str, session: ClientSession | None = None) -> None:
    # Balance must exist so an all-failed user (never credited) stays processing.
    users_collection.update_one(
        {"user_id": user_id, "pending_count": 0, "balance": {"$exists": True}},
        {"$set": {"status": "processed"}},
        session=session,
    )


def get_credit(task_id: str) -> dict[str, Any] | None:
    return credits_collection.find_one({"_id": task_id})


def ping() -> None:
    client.admin.command("ping")
