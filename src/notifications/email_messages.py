import datetime
from typing import Any

from src.events.models import Event
from src.users.models import User
from src.utils import EmailMessage


class FiveHoursBeforeEmailMessage(EmailMessage):
    """The message that is sent five hours before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что менее, чем через пять часов ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}"'


class OneDayBeforeEmailMessage(EmailMessage):
    """The message that is sent the day before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что менее, чем через одни сутки ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}"'


class OneWeekBeforeEmailMessage(EmailMessage):
    """The message that is sent the week before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что уже через неделю ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}"'


class EventChangedEmailMessage(EmailMessage):
    """The message that is sent when the address or datetime of the event change"""

    def __init__(self, event: Event, user: User, event_changes: dict[str, Any],
                 subject: str = 'Уведомление с событии!') -> None:
        super().__init__(event, user, subject)
        self.event_changes = event_changes

    def create_changes(self) -> str:
        changes = ''
        if 'datetime' in self.event_changes:
            past_datetime = self.event.datetime.strftime("%d-%m-%Y, %H:%M")
            new_datetime = datetime.datetime.fromisoformat(self.event_changes["datetime"]).strftime("%d-%m-%Y, %H:%M")
            changes += f'Дата и время: {past_datetime} -> {new_datetime}\n'

        if 'address' in self.event_changes:
            if self.event.address is not None:
                changes += f'Адрес: {self.event.address} ->'
            changes += self.event_changes["address"]

        return changes

    def create_payload(self) -> str:
        return f'Сообщаем вам, что данные события {self.event.name} ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}) ' \
               f'изменились. Вот измененные данные:\n' + self.create_changes()
