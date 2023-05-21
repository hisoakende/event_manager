import asyncio
import datetime
from typing import Any

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_shutdown, worker_init

import src.config
from src.database import db_start_up, db_shut_down
from src.notifications import tasks, config
from src.notifications.email_messages import FiveHoursBeforeEmailMessage, OneWeekBeforeEmailMessage, \
    OneDayBeforeEmailMessage
from src.notifications.service import receive_events_that_in_few_days_time, receive_events_for_this_and_next_day, \
    schedule_notifications_for_event

app = Celery(broker=config.BROKER_URL, include=['src.notifications.tasks'])

app.conf.enable_utc = False
app.conf.timezone = src.config.TIMEZONE


@app.task
def schedule_notifications() -> None:
    """The main function of scheduling notifications"""

    loop = asyncio.get_event_loop()
    now = datetime.datetime.now()

    events_in_week = loop.run_until_complete(receive_events_that_in_few_days_time(7, now))
    events_in_one_day = loop.run_until_complete(receive_events_that_in_few_days_time(1, now))

    for event in events_in_week:
        schedule_notifications_for_event(event, OneWeekBeforeEmailMessage, now, datetime.timedelta(days=7))

    for event in events_in_one_day:
        schedule_notifications_for_event(event, OneDayBeforeEmailMessage, now, datetime.timedelta(days=1))
        schedule_notifications_for_event(event, FiveHoursBeforeEmailMessage, now, datetime.timedelta(hours=5))


@app.on_after_configure.connect
def start_up(sender: Celery, **kwargs: Any) -> None:
    """
    The function that schedules notifications at application startup for events
    that the main scheduling function won't process
    """

    db_start_up()
    sender.add_periodic_task(crontab(hour=0, minute=0), schedule_notifications.s())


@worker_init.connect
def schedule_notifications_on_start_up(**kwargs: Any) -> None:
    """The function that schedules tasks when the application starts"""

    loop = asyncio.get_event_loop()
    now = datetime.datetime.now()
    events = loop.run_until_complete(receive_events_for_this_and_next_day(now))

    for event in events:
        if event.datetime - datetime.datetime.now() > datetime.timedelta(hours=15):
            schedule_notifications_for_event(event, OneDayBeforeEmailMessage, now, datetime.timedelta(days=1))

        if event.datetime - datetime.datetime.now() > datetime.timedelta(hours=2):
            schedule_notifications_for_event(event, FiveHoursBeforeEmailMessage, now, datetime.timedelta(hours=5))


@worker_shutdown.connect
def shut_down(**kwargs: Any) -> None:
    """The function that processes the stop of the celery app"""

    loop = asyncio.get_event_loop()
    loop.run_until_complete(db_shut_down())


EmailNotificationsSender = app.register_task(tasks.EmailNotificationsSender())
