from sqlalchemy import insert, select, text

from src import database
from src.redis_ import redis_engine
from src.service import execute_db_query, create_model, receive_model, update_models, delete_models, is_user_in_blacklist
from src.users.models import User, UserUpdate
from tests import config
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestExecuteDBQuery(DBProcessedIsolatedAsyncTestCase):

    async def test_executing(self) -> None:
        query = insert(User).values(id=2000, first_name='string', last_name='string',
                                    patronymic='string', email='string', password='string')
        await execute_db_query(query)
        async with database.Session() as session:
            user = await session.scalar(select(User).where(User.id == 2000))

        self.assertEqual(user.id, 2000)


class TestCreateModel(DBProcessedIsolatedAsyncTestCase):

    async def test_successful_creating(self) -> None:
        expected_result = True
        result = await create_model(User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                                         email='example@example.com', password='Example123'))
        self.assertEqual(result, expected_result)

        async with database.Session() as session:
            expected_id = await session.scalar(text("SELECT nextval('user_id_seq')")) - 1
        async with database.Session() as session:
            id_ = (await session.scalar(select(User).where(User.email == 'example@example.com'))).id
        self.assertEqual(id_, expected_id)

    async def test_failed_creating(self) -> None:
        async with database.Session() as session, session.begin():
            await session.execute(insert(User).values(id=3000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example1.com',
                                                      password='Example123'))
        user = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                    email='example@example1.com', password='Example123')

        async with database.Session() as session:
            next_id = await session.scalar(text("SELECT nextval('user_id_seq')")) + 1
            by_next_id = await session.scalar(select(User).where(User.id == next_id))
        self.assertIsNone(by_next_id)

        expected_result = False
        result = await create_model(user)
        self.assertEqual(result, expected_result)


class TestReceiveModel(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        async with database.Session() as session, session.begin():
            await session.execute(insert(User).values(id=4000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example2.com',
                                                      password='Example123'))
        expected_result = 4000
        result = (await receive_model(User, User.id == 4000)).id  # type: ignore
        self.assertEqual(result, expected_result)


class TestUpdatingModel(DBProcessedIsolatedAsyncTestCase):

    async def test_successful_updating(self) -> None:
        async with database.Session() as session, session.begin():
            await session.execute(insert(User).values(id=5000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example3.com',
                                                      password='Example123'))

        expected_result = 1
        result = await update_models(User, UserUpdate(first_name='Измененноеимя'), User.id == 5000)  # type: ignore
        self.assertEqual(result, expected_result)

        expected_name = 'Измененноеимя'
        async with database.Session() as session:
            name = (await session.scalar(select(User).where(User.id == 5000))).first_name
        self.assertEqual(name, expected_name)

    async def test_failed_updating(self) -> None:
        async with database.Session() as session, session.begin():
            await session.execute(insert(User).values(id=5000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example3.com',
                                                      password='Example123'))
            await session.execute(insert(User).values(id=6000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example4.com',
                                                      password='Example123'))

        expected_result = None
        result = await update_models(User, UserUpdate(email='example@example3.com'))
        self.assertEqual(result, expected_result)

        expected_email = 'example@example4.com'
        async with database.Session() as session:
            email = (await session.scalar(select(User).where(User.id == 6000))).email
        self.assertEqual(email, expected_email)


class TestDeleteModel(DBProcessedIsolatedAsyncTestCase):

    async def test_deleting(self) -> None:
        async with database.Session() as session, session.begin():
            await session.execute(insert(User).values(id=7000, first_name='Имя', last_name='Фамилия',
                                                      patronymic='Отчество', email='example@example5.com',
                                                      password='Example123'))
        expected_result = 1
        result = await delete_models(User, User.id == 7000)  # type: ignore
        self.assertEqual(result, expected_result)

        async with database.Session() as session:
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
