from unittest import TestCase

from src.redis_ import redis_engine
from src.users.service import add_user_to_blacklist
from tests import config


class TestAddUserToBlacklist(TestCase):

    def tearDown(self) -> None:
        redis_engine.delete(config.TEST_USERS_BLACKLIST_NAME)

    def test_addition(self) -> None:
        add_user_to_blacklist(10)

        expected_result = True
        result = redis_engine.sismember(config.TEST_USERS_BLACKLIST_NAME, 10)
        self.assertEqual(result, expected_result)
