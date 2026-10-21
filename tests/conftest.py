from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import credits_collection, ensure_indexes, users_collection


@pytest.fixture(autouse=True)
def clean_db() -> None:
    assert settings.mongo_db == "credits_test"
    ensure_indexes()
    credits_collection.delete_many({})
    users_collection.delete_many({})


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    from app.api import app
    from app.tasks import process_credit

    monkeypatch.setattr(
        process_credit,
        "apply_async",
        lambda *args, **kwargs: None,
    )
    with TestClient(app) as test_client:
        yield test_client
