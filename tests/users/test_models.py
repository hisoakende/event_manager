from unittest import TestCase
from unittest.mock import patch

from src.users.models import UserValidator
from src.users.utils import hash_password


class TestUserValidator(TestCase):

    def test_validate_full_name_successful(self) -> None:
        expected_result = 'Владимир'
        result = UserValidator.validate_full_name('ВЛАДимир')
        self.assertEqual(result, expected_result)

    def test_validate_full_name_failed(self) -> None:
        self.assertRaises(ValueError, UserValidator.validate_full_name, 'latin')
        self.assertRaises(ValueError, UserValidator.validate_full_name, 'Cпец символы111')
        self.assertRaises(ValueError, UserValidator.validate_full_name, '')
        self.assertRaises(ValueError, UserValidator.validate_full_name, 'а' * 36)

    def test_validate_password_successful(self) -> None:
        expected_result = f'salt${hash_password("Password123", "salt")}'
        with patch('src.users.models.get_random_string', return_value='salt'):
            result = UserValidator.validate_password('Password123')
        self.assertEqual(result, expected_result)

    def test_validate_password_failed(self) -> None:
        self.assertRaises(ValueError, UserValidator.validate_password, 'password')
        self.assertRaises(ValueError, UserValidator.validate_password, 'Password')
        self.assertRaises(ValueError, UserValidator.validate_password, 'Pa123')
        self.assertRaises(ValueError, UserValidator.validate_password, 'ПарольПароль')
        self.assertRaises(ValueError, UserValidator.validate_password, '')
        self.assertRaises(ValueError, UserValidator.validate_password, '12345343')
        self.assertRaises(ValueError, UserValidator.validate_password, 'password123')
