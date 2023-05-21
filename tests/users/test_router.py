import uuid as uuid_pkg
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import insert, select

from src.main import app
from src.redis_ import redis_engine
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
        with patch('src.users.router.BackgroundTasks.add_task') as mock, TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data)

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNone(user)

    async def test_incorrect_government_key(self) -> None:
        with patch('src.users.router.BackgroundTasks.add_task') as mock, TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data | {'government_key': '321'})

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNone(user)

    async def test_correct_government_key(self) -> None:
        with patch('src.users.router.BackgroundTasks.add_task') as mock, TestClient(app=app) as client:
            response = client.post('/users/', json=self.basic_request_data | {'government_key': config.GOVERNMENT_KEY})

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'email@email.com'))
        self.assertIsNone(user)

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


class TestUpdateUser(DBProcessedIsolatedAsyncTestCase):
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


class TestConfirmEmail(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_confirming(self) -> None:
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')
        confirmation_uuid = uuid_pkg.uuid4()
        redis_engine.set(f'{confirmation_uuid}-User', user.json())

        with TestClient(app=app) as client:
            response = client.post('/users/email-confirmation/', json={'confirmation_uuid': str(confirmation_uuid)})

        self.assertEqual(response.status_code, 201)

        expected_result = {'first_name': 'Имя', 'last_name': 'Фамилия',
                           'patronymic': 'Отчество', 'email': 'example@example1.com',
                           'is_government_worker': False}

        self.assertEqual(response.json(), expected_result)

        async with self.Session() as session:
            result = await session.scalar(select(User).where(User.email == 'example@example1.com'))
        self.assertIsNotNone(result)

    async def test_confirmation_uuid_is_invalid(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/users/email-confirmation/', json={'confirmation_uuid': str(uuid_pkg.uuid4())})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'confirmation_uuid'],
                                                       'msg': 'invalid value',
                                                       'type': 'value_error'}]})

    async def test_not_unique_email(self) -> None:
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')
        confirmation_uuid = uuid_pkg.uuid4()
        redis_engine.set(f'{confirmation_uuid}-User', user.json())

        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values({'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'example@example1.com',
                                                       'password': 'password', 'is_government_worker': False}))

        with TestClient(app=app) as client:
            response = client.post('/users/email-confirmation/', json={'confirmation_uuid': str(confirmation_uuid)})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'email'],
                                                       'msg': 'this email is already in use',
                                                       'type': 'value_error'}]})


class TestSendRecoveryUUID(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_sending(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values({'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'example@gmail.com',
                                                       'password': 'password', 'is_government_worker': False}))

        with patch('src.users.router.BackgroundTasks.add_task') as mock, TestClient(app=app) as client:
            response = client.post('/users/password-recovery/', json={'email': 'example@gmail.com'})

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 204)

    async def test_user_doesnt_exist(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/users/password-recovery/', json={'email': 'example@gmail.com'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'email'],
                                                       'msg': 'user with this email not found',
                                                       'type': 'value_error'}]})


class TestRecoverPassword(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_recovering(self) -> None:
        recovery_uuid = uuid_pkg.uuid4()
        redis_engine.set(str(recovery_uuid), 2121)

        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values({'id': 2121, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'example@gmail.com',
                                                       'password': 'password', 'is_government_worker': False}))

        with TestClient(app=app) as client:
            response = client.post(f'/users/password-recovery/{recovery_uuid}', json={'password': 'Example123'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            result = await session.scalar(select(User).where(User.password == 'password'))
        self.assertIsNone(result)

    async def test_user_id_is_none(self) -> None:
        with TestClient(app=app) as client:
            response = client.post(f'/users/password-recovery/{uuid_pkg.uuid4()}', json={'password': 'Example123'})

        self.assertEqual(response.status_code, 404)

    async def test_invalid_password(self) -> None:
        recovery_uuid = uuid_pkg.uuid4()
        redis_engine.set(str(recovery_uuid), 2121)

        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values({'id': 2323, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'example@gmail.com',
                                                       'password': 'password', 'is_government_worker': False}))

        with TestClient(app=app) as client:
            response = client.post(f'/users/password-recovery/{recovery_uuid}', json={'password': 'example'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'password'],
                                                       'msg': 'invalid value',
                                                       'type': 'value_error'}]})

        async with self.Session() as session:
            result = await session.scalar(select(User).where(User.password == 'password'))
        self.assertIsNotNone(result)
