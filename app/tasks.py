import logging

from celery import Task
from pymongo.errors import PyMongoError

from app.celery_app import celery
from app.repository import apply_credit, fail_credit

logger = logging.getLogger(__name__)


class CreditTask(Task):
    autoretry_for = (PyMongoError,)
    retry_backoff = True
    retry_jitter = True
    max_retries = 5

    def on_failure(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        einfo: object,
    ) -> None:
        fail_credit(str(args[0]), str(exc))


@celery.task(base=CreditTask, name="app.tasks.process_credit")
def process_credit(task_id: str) -> None:
    if apply_credit(task_id):
        logger.info("event=credit_applied task_id=%s", task_id)
    else:
        logger.info("event=credit_duplicate_skipped task_id=%s", task_id)
