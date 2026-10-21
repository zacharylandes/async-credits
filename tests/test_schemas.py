from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import CreditRequest


def test_credit_request_valid() -> None:
    request = CreditRequest(user_id="alice", amount=Decimal("10.50"))
    assert request.user_id == "alice"
    assert request.amount == Decimal("10.50")


def test_credit_request_strips_user_id() -> None:
    request = CreditRequest(user_id="  alice  ", amount=Decimal("1.00"))
    assert request.user_id == "alice"


def test_credit_request_rejects_empty_user_id() -> None:
    with pytest.raises(ValidationError):
        CreditRequest(user_id="", amount=Decimal("1.00"))


def test_credit_request_rejects_long_user_id() -> None:
    with pytest.raises(ValidationError):
        CreditRequest(user_id="a" * 65, amount=Decimal("1.00"))


def test_credit_request_rejects_non_positive_amount() -> None:
    with pytest.raises(ValidationError):
        CreditRequest(user_id="alice", amount=Decimal("0"))
    with pytest.raises(ValidationError):
        CreditRequest(user_id="alice", amount=Decimal("-1.00"))


def test_credit_request_rejects_too_many_decimal_places() -> None:
    with pytest.raises(ValidationError):
        CreditRequest(user_id="alice", amount=Decimal("1.001"))
