from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError

from app.db import credits_collection, users_collection
from app.repository import apply_credit, get_credit
from app.tasks import process_credit


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_credit(client: TestClient) -> None:
    response = client.post(
        "/credits",
        json={"user_id": "alice", "amount": "10.00"},
    )
    assert response.status_code == 202
    task_id = response.json()["task_id"]
    credit = get_credit(task_id)
    assert credit is not None
    assert credit["status"] == "pending"
    apply_credit(task_id)
    status_response = client.get(f"/credits/{task_id}")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["task_id"] == task_id
    assert body["user_id"] == "alice"
    assert Decimal(body["amount"]) == Decimal("10.00")
    assert body["status"] == "processed"


def test_create_credit_validation_error(client: TestClient) -> None:
    response = client.post(
        "/credits",
        json={"user_id": "", "amount": "10.00"},
    )
    assert response.status_code == 422


def test_get_credit_not_found(client: TestClient) -> None:
    response = client.get("/credits/missing")
    assert response.status_code == 404


def test_publish_failure_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise OperationalError("broker down")

    monkeypatch.setattr(process_credit, "apply_async", boom)
    response = client.post(
        "/credits",
        json={"user_id": "alice", "amount": "1.00"},
    )
    assert response.status_code == 503
    credit = credits_collection.find_one({"user_id": "alice"})
    assert credit is not None
    assert credit["status"] == "failed"


def test_two_posts_sum_balance(client: TestClient) -> None:
    first = client.post("/credits", json={"user_id": "alice", "amount": "10.00"})
    second = client.post("/credits", json={"user_id": "alice", "amount": "2.50"})
    assert first.status_code == 202
    assert second.status_code == 202
    apply_credit(first.json()["task_id"])
    apply_credit(second.json()["task_id"])
    user = users_collection.find_one({"user_id": "alice"})
    assert user is not None
    assert user["balance"].to_decimal() == Decimal("12.50")
    assert user["status"] == "processed"
