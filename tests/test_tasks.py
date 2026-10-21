from decimal import Decimal

from app.db import users_collection
from app.repository import get_credit, register_credit
from app.tasks import process_credit


def test_process_credit_applies() -> None:
    register_credit("t1", "alice", Decimal("3.00"))
    process_credit("t1")
    credit = get_credit("t1")
    assert credit is not None
    assert credit["status"] == "processed"
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("3.00")
    assert user["status"] == "processed"


def test_process_credit_duplicate_skipped() -> None:
    register_credit("t1", "alice", Decimal("3.00"))
    process_credit("t1")
    process_credit("t1")
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("3.00")


def test_on_failure_fails_credit() -> None:
    register_credit("t1", "alice", Decimal("3.00"))
    process_credit.on_failure(RuntimeError("boom"), "celery-task-id", ("t1",), {}, None)
    credit = get_credit("t1")
    assert credit is not None
    assert credit["status"] == "failed"
    assert credit["error"] == "boom"
