from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from app.db import users_collection
from app.repository import apply_credit, fail_credit, get_credit, register_credit


def test_register_and_apply_credit() -> None:
    register_credit("t1", "alice", Decimal("10.00"))
    assert apply_credit("t1") is True
    credit = get_credit("t1")
    assert credit is not None
    assert credit["status"] == "processed"
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("10.00")
    assert user["pending_count"] == 0
    assert user["status"] == "processed"


def test_apply_credit_idempotent() -> None:
    register_credit("t1", "alice", Decimal("5.00"))
    assert apply_credit("t1") is True
    assert apply_credit("t1") is False
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("5.00")


def test_fail_credit() -> None:
    register_credit("t1", "alice", Decimal("5.00"))
    assert fail_credit("t1", "boom") is True
    credit = get_credit("t1")
    assert credit is not None
    assert credit["status"] == "failed"
    assert credit["error"] == "boom"
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["pending_count"] == 0
    assert "balance" not in user
    assert user["status"] == "processed"


def test_fail_credit_idempotent() -> None:
    register_credit("t1", "alice", Decimal("5.00"))
    assert fail_credit("t1", "boom") is True
    assert fail_credit("t1", "again") is False


def test_two_credits_sum_balance() -> None:
    register_credit("t1", "alice", Decimal("10.00"))
    register_credit("t2", "alice", Decimal("2.50"))
    assert apply_credit("t1") is True
    assert apply_credit("t2") is True
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("12.50")
    assert user["status"] == "processed"


def test_concurrent_apply_same_credit_once() -> None:
    register_credit("t1", "alice", Decimal("7.00"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(apply_credit, "t1") for _ in range(8)]
        results = [future.result() for future in as_completed(futures)]
    assert results.count(True) == 1
    assert results.count(False) == 7
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("7.00")
