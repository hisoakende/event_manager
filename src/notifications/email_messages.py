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


class OneWeekBeforeEmailBefore(EmailMessage):
    """The message that is sent the week before the event"""

    def create_payload(self) -> str:
        return f'Сообщаем Вам, что уже через неделю ' \
               f'({self.event.datetime.strftime("%d-%m-%Y, %H:%M")}), ' \
               f'состоится событие "{self.event.name}"'
