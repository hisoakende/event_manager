from unittest.mock import Mock

from fastapi import HTTPException

from src.auth.models import RefreshToken
from src.dependencies import authorize_user
from src.redis_ import redis_engine
from src.users.models import User
from tests import config
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestAuthorizeUser(DBProcessedIsolatedAsyncTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.authorise = Mock()
        self.authorise.get_jwt_subject = lambda: 1000
        self.authorise.get_raw_jwt = lambda: {'is_government_worker': False}
        self.authorise._token = 'token'

        async with self.Session() as session:
            session.add(User(id=1000, first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                             email='example@email.com', password='Example123'))
            await session.commit()
            session.add(RefreshToken(user_id=1000, value='token'))
            await session.commit()

    async def test_access_token(self) -> None:
        expected_result = 1000
        result = await authorize_user()(self.authorise)
        self.assertEqual(result, expected_result)

    async def test_refresh_token_exist(self) -> None:
        expected_result = 1000
        result = await authorize_user(refresh_token=True)(self.authorise)
        self.assertEqual(result, expected_result)

    async def test_refresh_token_doesnt_exist(self) -> None:
        self.authorise._token = 'non-existent token'

        with self.assertRaises(HTTPException):
            await authorize_user(refresh_token=True)(self.authorise)

    async def test_user_in_blacklist(self) -> None:
        redis_engine.sadd(config.TEST_USERS_BLACKLIST_NAME, 999)
        self.authorise.get_jwt_subject = lambda: 999

        with self.assertRaises(HTTPException):
            await authorize_user()(self.authorise)

    async def test_user_is_not_gov_worker(self) -> None:
        with self.assertRaises(HTTPException):
            await authorize_user(is_government_worker=True)(self.authorise)

    async def test_user_is_gov_worker(self) -> None:
        self.authorise.get_raw_jwt = lambda: {'is_government_worker': True}

        expected_result = 1000
        result = await authorize_user(is_government_worker=True)(self.authorise)
        self.assertEqual(result, expected_result)
