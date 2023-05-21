import asyncio
import datetime

from sqlalchemy import select, func

import src.notifications.celery_
from src.events.models import Event
from src.service import execute_db_query
from src.utils import EmailMessage


async def receive_events_that_in_few_days_time(day_count: int, datetime_: datetime.datetime) -> list[Event]:
    """
    The function that schedules notifications at application startup for events
    that the main scheduling function won't process
    """

    in_day_count = (datetime_ + datetime.timedelta(days=day_count)).date()
    query = select(Event).where(func.date(Event.datetime) == in_day_count)
    return (await execute_db_query(query)).scalars().fetchall()


async def receive_events_for_this_and_next_day(datetime_: datetime.datetime) -> list[Event]:
    """The function that returns the events that will occur on the given day and the next"""

    edge = (datetime_ + datetime.timedelta(days=2)).replace(hour=0, minute=0)
    query = select(Event).where(Event.datetime >= datetime_, Event.datetime < edge)
    return (await execute_db_query(query)).scalars().fetchall()


def get_countdown(start: datetime.datetime, end: datetime.datetime) -> int:
    """The function that returns the delay in seconds"""

    if start > end:
        return 0
    return int((end - start).total_seconds())


def schedule_notifications_for_event(event: Event, message_class: type[EmailMessage],
                                     datetime_: datetime.datetime,
                                     timedelta: datetime.timedelta) -> None:
    """The function that schedules notifications for the event"""

    notifications_datetime = event.datetime - timedelta
    countdown = get_countdown(datetime_, notifications_datetime)
    src.notifications.celery_.EmailNotificationsSender.apply_async(
        args=(event.uuid, message_class.__name__, event.datetime),
        countdown=countdown
    )
