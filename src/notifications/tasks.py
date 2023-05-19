import asyncio
import datetime
import json
from typing import Any

from celery import Task
from sqlalchemy import select

import src.config
from src import database
from src.events.models import Event
from src.events.service import create_receiving_subs_to_event_union_query_from_db
from src.notifications.email_messages import EventNotificationEmailMessage
from src.service import receive_model, send_email
from src.users.models import User


class EmailNotificationsSender(Task):
    """The class that processes sending notifications in the form of email messages"""

    def __init__(self, event: Event | None = None) -> None:
        self.event = event

    async def send_notification(self, user: User, message_class: type[EventNotificationEmailMessage],
                                **kwargs: Any) -> None:
        """The method that sends one notification"""

        message = message_class(event=self.event, user=user, **kwargs)  # type: ignore
        await send_email(message)

    async def send_notifications(self, message_class: type[EventNotificationEmailMessage], **kwargs: Any) -> None:
        """The method that sends notifications to all subscribers"""

        query = create_receiving_subs_to_event_union_query_from_db(self.event.uuid,  # type: ignore
                                                                   self.event.gov_structure_uuid)  # type: ignore
        query = select(User).from_statement(query)

        async with database.Session() as session:
            result = await session.stream_scalars(query)
            async for partition in result.partitions(src.config.DATABASE_CURSOR_SIZE):
                coroutines = [self.send_notification(user, message_class, **kwargs) for user in partition]
                await asyncio.gather(*coroutines, return_exceptions=True)

    def run(self, event: str, message_class_name: str,
            datetime_: str | None = None, is_json: bool = False,
            **kwargs: Any) -> None:
        """The method that starts when the event is processed"""

        loop = asyncio.get_event_loop()
        if is_json:
            self.event = Event(**json.loads(event))

        else:
            self.event = loop.run_until_complete(receive_model(Event, Event.uuid == event))  # type: ignore
            if self.event is None or (datetime_ and self.event.datetime != datetime.datetime.fromisoformat(datetime_)):
                return

        message_class = EventNotificationEmailMessage.messages_classes[message_class_name]
        loop.run_until_complete(self.send_notifications(message_class, **kwargs))
