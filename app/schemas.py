from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

UserId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64, strip_whitespace=True),
]
Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class CreditRequest(BaseModel):
    user_id: UserId
    amount: Amount


class CreditAccepted(BaseModel):
    task_id: str


class CreditStatus(BaseModel):
    task_id: str
    user_id: str
    amount: Decimal
    status: Literal["pending", "processed", "failed"]
