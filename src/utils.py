import typing
from abc import abstractmethod, ABC
from email.mime.text import MIMEText
from typing import Any

from pydantic import root_validator
from sqlmodel import SQLModel

import src.config

if typing.TYPE_CHECKING:
    from src.users.models import User


class ChangesAreNotEmptyMixin(SQLModel):

    @root_validator(pre=True)
    def changes_are_not_empty(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        The validator that checks for the existence of at least one field in the model

        This is necessary for the correct update of the data
        """

        if all(field not in cls.schema_json() for field in values):
            raise ValueError('you must specify at least one field')
        return values


class EmailMessage(ABC):
    """The base class that processes the creation of the email"""

    def __init__(self, user: typing.Optional['User'], subject: str) -> None:
        self.user = user
        self.subject = subject

    def create_welcome_message(self) -> str:
        if self.user is None:
            return f'Здравствуйте!\n'
        return f'Здравствуйте, {self.user.first_name} {self.user.patronymic}!\n'

    @abstractmethod
    def create_payload(self) -> str:
        """The method that creates the content of the message"""

    def create(self) -> MIMEText:
        """The method that creates a message ready to be sent"""

        welcome_message = self.create_welcome_message()
        payload = welcome_message + self.create_payload()

        message = MIMEText(payload)
        message['Subject'] = self.subject
        message['From'] = src.config.EMAIL_LOCAL_ADDRESS
        if self.user is not None:
            message['To'] = self.user.email

        return message
