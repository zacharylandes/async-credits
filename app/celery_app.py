from celery import Celery

from app.config import settings
from app.logging import configure_logging

configure_logging()

celery = Celery("credits", broker=settings.broker_url)
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_backend=None,
    imports=("app.tasks",),
)
