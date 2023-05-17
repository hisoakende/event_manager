import asyncio
from typing import Any

from celery import Celery
from celery.apps.worker import Worker
from celery.signals import worker_init, worker_shutdown

from src.database import db_start_up, db_shut_down

app = Celery(broker='redis://localhost//', include=['src.notifications.tasks'])


@worker_init.connect
def start_up(sender: Worker, headers: Any = None, body: Any = None, **kwargs: Any) -> None:
    """The function that processes the start of the celery app"""

    db_start_up()


@worker_shutdown.connect()
def shut_down(sender: Worker, headers: Any = None, body: Any = None, **kwargs: Any) -> None:
    """The function that processes the stop of the celery app"""

    asyncio.run(db_shut_down())
