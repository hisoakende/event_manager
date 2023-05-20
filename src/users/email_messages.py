import uuid as uuid_pkg

from src.users.models import User
from src.utils import EmailMessage


class ConfirmUserEmailEmailMessage(EmailMessage):
    """The message that is sent to confirm the email of the user"""

    def __init__(self, user: User, confirmation_uuid: uuid_pkg.UUID) -> None:
        super().__init__(user, 'Подтверждение email')
        self.confirmation_uuid = confirmation_uuid

    def create_payload(self) -> str:
        return f'Ваш код подтверждения:\n' \
               f'{self.confirmation_uuid}\n' \
               f'Код действителен в течение 30 минут.'


class RecoveryPasswordEmailMessage(EmailMessage):
    """The message that is sent to recover the password"""

    def __init__(self, user: User, recovery_url: str) -> None:
        super().__init__(user, 'Восстановление пароля')
        self.recovery_url = recovery_url

    def create_payload(self) -> str:
        return f'Ваша ссылка для восстановления пароля:\n' \
               f'{self.recovery_url}\n' \
               f'Cсылка действительна в течение 30 минут.'
