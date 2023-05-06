from unittest import TestCase
from unittest.mock import patch

from src.users.utils import get_random_string, hash_password, verify_password


class TestGetRandomString(TestCase):

    def test_getting(self) -> None:
        expected_result = 'abcdeabcde'
        with patch('random.choices', return_value=['a', 'b', 'c', 'd', 'e', 'a', 'b', 'c', 'd', 'e']):
            result = get_random_string()
        self.assertEqual(result, expected_result)


class TestVerifyPassword(TestCase):

    def test_successful_verification(self) -> None:
        hashed_password = f'salt${hash_password("password", "salt")}'

        expected_result = True
        result = verify_password('password', hashed_password)
        self.assertEqual(result, expected_result)

    def test_failed_verification(self) -> None:
        hashed_password = f'salt${hash_password("password", "salt")}'

        expected_result = False
        result = verify_password('password1', hashed_password)
        self.assertEqual(result, expected_result)
