from fastapi.testclient import TestClient
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import insert, select

from src.main import app
from src.users import config
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestCreateUser(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    @classmethod
    def setUpClass(cls) -> None:
        cls.basic = {'first_name': 'Имя', 'last_name': 'Фамилия',
                     'patronymic': 'Отчество', 'email': 'email@email.com'}
        cls.basic_request_data = cls.basic | {'password': 'Password123'}

    async def test_user_is_not_gov_worker(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), self.basic | {'is_government_worker': False})

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNotNone(user)

    async def test_incorrect_government_key(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data | {'government_key': '321'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), self.basic | {'is_government_worker': False})

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNotNone(user)

    async def test_correct_government_key(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data | {'government_key': config.GOVERNMENT_KEY})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), self.basic | {'is_government_worker': True})

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNotNone(user)

    async def test_not_unique_email(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(id=7000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='email@email.com',
                                                      password='Example123'))
        with TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'email'],
                                                       'msg': 'this email is already in use',
                                                       'type': 'value_error'}]})


class TestReceiveUser(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    basic = {'first_name': 'Имя', 'last_name': 'Фамилия',
             'patronymic': 'Отчество', 'email': 'email@email.com'}

    async def test_receiving(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(self.basic | {'id': 8000, 'password': 'Password123'}))
        token = AuthJWT().create_access_token(subject=8000, user_claims={'is_government_worker': False})

        with TestClient(app=app) as client:
            response = client.get('/users/self/', headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.basic | {'is_government_worker': False})


class TestChangeUser(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    basic = {'first_name': 'Имя', 'last_name': 'Фамилия',
             'patronymic': 'Отчество', 'email': 'email@email.com'}

    async def test_successful_changing(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(self.basic | {'id': 9000, 'password': 'Password123'}))
        token = AuthJWT().create_access_token(subject=9000, user_claims={'is_government_worker': False})

        with TestClient(app=app) as client:
            response = client.patch('/users/self/', json={'first_name': 'Изменненоеимя'},
                                    headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.basic | {'is_government_worker': False, 'first_name': 'Изменненоеимя'})

        expected_result = 'Изменненоеимя'
        async with self.Session() as session:
            result = (await session.scalar(select(User).where(User.email == 'email@email.com'))).first_name
        self.assertEqual(result, expected_result)

    async def test_failed_changing(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(self.basic | {'id': 10000, 'password': 'Password123'}))
            await session.execute(insert(User).values(self.basic | {'id': 10001, 'password': 'Password123',
                                                                    'email': 'email1@email.com'}))
        token = AuthJWT().create_access_token(subject=10000, user_claims={'is_government_worker': False})

        with TestClient(app=app) as client:
            response = client.patch('/users/self/', json={'email': 'email1@email.com'},
                                    headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'email'],
                                                       'msg': 'this email is already in use',
                                                       'type': 'value_error'}]})

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNotNone(user)


class TestDeleteUser(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    basic = {'first_name': 'Имя', 'last_name': 'Фамилия',
             'patronymic': 'Отчество', 'email': 'email@email.com'}

    async def test_deleting(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(self.basic | {'id': 11000, 'password': 'Password123'}))
        token = AuthJWT().create_access_token(subject=11000, user_claims={'is_government_worker': False})

        with TestClient(app=app) as client:
            response = client.delete('/users/self/', headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            result = await session.scalar(select(User).where(User.id == 11000))
        self.assertIsNone(result)
