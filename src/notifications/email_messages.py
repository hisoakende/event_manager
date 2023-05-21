import datetime
from abc import ABC
from typing import Any

from src.events.models import Event
from src.users.models import User
from src.utils import EmailMessage


class EventNotificationEmailMessage(EmailMessage, ABC):
    """The base class for email notifications"""

    messages_classes: dict[str, type['EventNotificationEmailMessage']] = {}

    def __init__(self, event: 'Event', user: 'User') -> None:
        super().__init__(user, 'Уведомление o событии!')
        self.event = event

    def __init_subclass__(cls) -> None:
        EventNotificationEmailMessage.messages_classes[cls.__name__] = cls


class FiveHoursBeforeEmailMessage(EventNotificationEmailMessage):
    """The message that is sent five hours before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что менее, чем через пять часов ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}".'


class OneDayBeforeEmailMessage(EventNotificationEmailMessage):
    """The message that is sent the day before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что менее, чем через одни сутки ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}".'


class OneWeekBeforeEmailMessage(EventNotificationEmailMessage):
    """The message that is sent the week before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что уже через неделю ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}".'


class EventChangedEmailMessage(EventNotificationEmailMessage):
    """The message that is sent when the address or datetime of the event change"""

    def __init__(self, event: Event, user: User, event_changes: dict[str, Any]) -> None:
        super().__init__(event, user)
        self.event_changes = event_changes

    def create_changes(self) -> str:
        changes = ''

        if 'datetime' in self.event_changes:
            past_datetime = self.event.datetime.strftime("%d-%m-%Y, %H:%M")
            new_datetime = datetime.datetime.fromisoformat(self.event_changes["datetime"]).strftime("%d-%m-%Y, %H:%M")
            changes += f'Дата и время: {past_datetime} -> {new_datetime}\n'

        if 'address' in self.event_changes:
            if self.event.address is None:
                self.event.address = 'не указан'
            if self.event_changes['address'] is None:
                self.event_changes['address'] = 'не указан'
            changes += f'Адрес: {self.event.address} -> {self.event_changes["address"]}'

        return changes

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что данные события "{self.event.name}" ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}) ' \
               f'изменились. Вот измененные данные:\n' + self.create_changes()


class EventCanceledEmailMessage(EventNotificationEmailMessage):
    """The message that is sent when the event is canceled"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что событие "{self.event.name}" ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}) ' \
               f'отменено. Если будет принято решение о проведение этого события, ' \
               f'мы Вам сообщим.'


class HostingEventEmailMessage(EventNotificationEmailMessage):
    """The message that is sent when the canceled event is held"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что отмененное событие "{self.event.name}" ' \
               f'будет проведено {self.event.datetime.strftime("%d-%m-%Y в %H:%M")}.'
