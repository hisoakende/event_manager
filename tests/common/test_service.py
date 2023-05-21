import json
import uuid as uuid_pkg

from unittest import TestCase

from asyncpg import UniqueViolationError
from sqlalchemy import insert, select, text
from sqlmodel import SQLModel

from src.events.models import Event
from src.redis_ import redis_engine
from src.service import execute_db_query, create_model, receive_model, update_models, delete_models, \
    is_user_in_blacklist, set_unconfirmed_email_data, receive_unconfirmed_email_data, delete_unconfirmed_email_data
from src.users.models import User, UserUpdate
from tests import config
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestExecuteDBQuery(DBProcessedIsolatedAsyncTestCase):

    async def test_executing(self) -> None:
        query = insert(User).values(id=2000, first_name='string', last_name='string',
                                    patronymic='string', email='string', password='string')
        await execute_db_query(query)
        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.id == 2000))

        self.assertEqual(user.id, 2000)


class TestCreateModel(DBProcessedIsolatedAsyncTestCase):

    async def test_successful_creating(self) -> None:
        await create_model(User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                                email='example@example.com', password='Example123'))

        async with self.Session() as session:
            user = await session.scalar(select(User).where(User.email == 'example@example.com'))
        self.assertIsNotNone(user)

    async def test_failed_creating(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(id=3000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example1.com',
                                                      password='Example123'))
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')

        with self.assertRaises(UniqueViolationError):
            await create_model(user)

        async with self.Session() as session:
            id_ = await session.scalar(text("SELECT nextval('user_id_seq')")) - 1
            by_id = await session.scalar(select(User).where(User.id == id_))
        self.assertIsNone(by_id)


class TestReceiveModel(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(id=4000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example2.com',
                                                      password='Example123'))
        expected_result = 4000
        result = (await receive_model(User, User.id == 4000)).id  # type: ignore
        self.assertEqual(result, expected_result)


class TestUpdatingModel(DBProcessedIsolatedAsyncTestCase):

    async def test_updating(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(id=5000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example3.com',
                                                      password='Example123'))

        expected_result = 1
        result = await update_models(User, UserUpdate(first_name='Измененноеимя'), User.id == 5000)  # type: ignore
        self.assertEqual(result, expected_result)

        expected_name = 'Измененноеимя'
        async with self.Session() as session:
            name = (await session.scalar(select(User).where(User.id == 5000))).first_name
        self.assertEqual(name, expected_name)


class TestDeleteModel(DBProcessedIsolatedAsyncTestCase):

    async def test_deleting(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(User).values(id=7000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example5.com',
                                                      password='Example123'))
        expected_result = 1
        result = await delete_models(User, User.id == 7000)  # type: ignore
        self.assertEqual(result, expected_result)

        async with self.Session() as session:
            result = await session.scalar(select(User).where(User.id == 7000))
        self.assertIsNone(result)


class TestIsUserInBlacklist(DBProcessedIsolatedAsyncTestCase):

    @classmethod
    def tearDownClass(cls) -> None:
        redis_engine.delete(config.TEST_USERS_BLACKLIST_NAME)

    async def test_user_is_in_blacklist(self) -> None:
        redis_engine.sadd(config.TEST_USERS_BLACKLIST_NAME, 8000)

        expected_result = True
        result = is_user_in_blacklist(8000)
        self.assertEqual(result, expected_result)

    async def test_user_is_not_in_blacklist(self) -> None:
        expected_result = False
        result = is_user_in_blacklist(9000)
        self.assertEqual(result, expected_result)


class TestSetUnconfirmedEmailData(TestCase):

    def test_setting(self) -> None:
        confirmation_uuid = uuid_pkg.uuid4()
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')

        set_unconfirmed_email_data(confirmation_uuid, user)  # type: ignore
        expected_result = user.json()
        result = redis_engine.get(f'{confirmation_uuid}-User')
        self.assertEqual(result, expected_result)

        redis_engine.delete(f'{confirmation_uuid}-User')


class TestReceiveUnconfirmedEmailData(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.confirmation_uuid = uuid_pkg.uuid4()
        cls.user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                        email='example@example1.com', password='Example123')

    def test_data_is_not_None(self) -> None:
        redis_engine.set(f'{self.confirmation_uuid}-User', self.user.json())

        expected_result = self.user
        result = receive_unconfirmed_email_data(self.confirmation_uuid, User)
        self.assertEqual(result, expected_result)

    def test_data_is_None(self) -> None:
        result = receive_unconfirmed_email_data(uuid_pkg.uuid4(), User)
        self.assertIsNone(result)


class TestDeleteUnconfirmedEmailData(TestCase):

    def test_deleting(self) -> None:
        confirmation_uuid = uuid_pkg.uuid4()
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')
        redis_engine.set(f'{confirmation_uuid}-User', user.json())

        delete_unconfirmed_email_data(confirmation_uuid, User)

        result = redis_engine.get(f'{confirmation_uuid}-User')
        self.assertIsNone(result)
