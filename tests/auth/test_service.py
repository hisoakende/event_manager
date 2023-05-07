from sqlalchemy import insert

from src import database
from src.auth.models import RefreshToken
from src.auth.service import does_refresh_token_exist
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestDoesRefreshTokenExist(DBProcessedIsolatedAsyncTestCase):

    async def test_token_exist(self) -> None:
        async with database.Session() as session, session.begin():
            await session.execute(insert(User).values({'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'id': 14000, 'password': 'Password123'}))
            await session.execute(insert(RefreshToken).values({'user_id': 14000, 'value': 'token'}))

        expected_result = True
        result = await does_refresh_token_exist(RefreshToken(user_id=14000, value='token'))
        self.assertEqual(result, expected_result)

    async def test_token_does_not_exist(self) -> None:
        expected_result = False
        result = await does_refresh_token_exist(RefreshToken(user_id=123, value='invalid token'))
        self.assertEqual(result, expected_result)
