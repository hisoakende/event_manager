from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import insert, select

from src.auth.models import RefreshToken
from src.main import app
from src.users.models import User
from src.users.utils import hash_password
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestLogin(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        user = {'id': 9000, 'password': f'salt${hash_password("Password123", "salt")}', 'first_name': 'Имя',
                'last_name': 'Фамилия', 'patronymic': 'Отчество', 'email': 'email@email.com'}
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(user))

    async def test_successful_login(self) -> None:
        with patch('src.auth.router.create_tokens_values', return_value=('access', 'refresh')), \
                TestClient(app=app) as client:
            response = client.post('/auth/login/', json={'email': 'email@email.com', 'password': 'Password123'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'access_token': 'access', 'refresh_token': 'refresh'})

    async def test_invalid_email(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/auth/login/', json={'email': 'invalid@email.com', 'password': 'Password123'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'email'],
                                                       'msg': 'user with this email does not exist',
                                                       'type': 'value_error'}]})

    async def test_invalid_password(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/auth/login/', json={'email': 'email@email.com', 'password': 'InvalidPassword'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'password'],
                                                       'msg': 'invalid password',
                                                       'type': 'value_error'}]})


class TestLogout(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_logout(self) -> None:
        token = AuthJWT().create_refresh_token(subject=12000, user_claims={'is_government_worker': False})
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values({'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'id': 12000, 'password': 'Password123'}))
            await session.execute(insert(RefreshToken).values({'user_id': 12000, 'value': token}))

        with TestClient(app=app) as client:
            response = client.post('/auth/logout/', headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            token_from_db = await session.scalar(select(RefreshToken).where(RefreshToken.user_id == 12000,
                                                                            RefreshToken.value == token))
        self.assertIsNone(token_from_db)


class TestUpdateAccessToken(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_updating(self) -> None:
        token = AuthJWT().create_refresh_token(subject=13000, user_claims={'is_government_worker': False})
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values({'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'id': 13000, 'password': 'Password123'}))
            await session.execute(insert(RefreshToken).values({'user_id': 13000, 'value': token}))

        with patch('src.auth.router.create_tokens_values', return_value=('access', 'refresh')), \
                TestClient(app=app) as client:
            response = client.post('/auth/refresh/', headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'access_token': 'access', 'refresh_token': 'refresh'})

        async with self.Session() as session:
            token_from_db = await session.scalars(select(RefreshToken).where(RefreshToken.user_id == 13000))
        self.assertEqual(token_from_db.one().value, 'refresh')
