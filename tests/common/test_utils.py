from unittest import TestCase

from src.users.models import User, UserUpdate
from src.utils import ChangesAreNotEmptyMixin, EmailMessage


class TestChangeAreNotEmptyMixin(TestCase):

    def test_changes_are_empty(self) -> None:
        with self.assertRaises(ValueError):
            ChangesAreNotEmptyMixin.changes_are_not_empty({})

    def test_changes_are_not_empty(self) -> None:
        expected_result = {'first_name': 'Измененноеимя'}
        result = UserUpdate.changes_are_not_empty({'first_name': 'Измененноеимя'})
        self.assertEqual(result, expected_result)


class TestEmailMessage(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.message_class = type('TestEmailMessage', (EmailMessage,), {'create_payload': lambda self_: 'str'})

    def test_create_welcome_message_user_is_None(self) -> None:
        expected_result = 'Здравствуйте!\n'
        result = self.message_class(None, 'subject').create_welcome_message()
        self.assertEqual(result, expected_result)

    def test_create_welcome_message_user_is_not_None(self) -> None:
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')

        expected_result = self.message_class(user, 'subject').create_welcome_message()
        result = 'Здравствуйте, Имя Отчество!\n'
        self.assertEqual(result, expected_result)

    def test_create_user_is_None(self) -> None:
        message = self.message_class(None, 'subject')

        result = message.create()['To']
        self.assertIsNone(result)

    def test_create_user_is_not_None(self) -> None:
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')
        message = self.message_class(user, 'subject')

        result = message.create()['To']
        self.assertIsNotNone(result)
