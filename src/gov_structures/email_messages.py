import uuid as uuid_pkg
from email.mime.text import MIMEText

from src.gov_structures.models import GovStructure
from src.utils import EmailMessage


class ConfirmGovStructureEmailEmailMessage(EmailMessage):
    """The message that is sent to confirm the email of the government structure"""

    def __init__(self, gov_structure: GovStructure, confirmation_uuid: uuid_pkg.UUID):
        super().__init__(None, 'Подтверждение email')
        self.gov_structure = gov_structure
        self.confirmation_uuid = confirmation_uuid

    def create_payload(self) -> str:
        return f'Код подтверждения для правительственной структуры "{self.gov_structure.name}":\n' \
               f'{self.confirmation_uuid}\n' \
               f'Код действителен в течение 30 минут'

    def create(self) -> MIMEText:
        message = super().create()
        message['To'] = self.gov_structure.email
        return message
