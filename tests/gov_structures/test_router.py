import uuid as uuid_pkg
from unittest.mock import patch

from src.redis_ import redis_engine
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import select, insert
from starlette.testclient import TestClient

from src.gov_structures.models import GovStructure, GovStructureSubscription
from src.main import app
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestCreateGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_creating(self) -> None:
        token = AuthJWT().create_access_token(subject=1010, user_claims={'is_government_worker': True})
        with patch('src.gov_structures.router.BackgroundTasks.add_task') as mock, TestClient(app=app) as client:
            response = client.post('/government-structures/',
                                   headers={'Authorization': f'Bearer {token}'},
                                   json={'name': 'Government Structure',
                                         'email': 'example@gmail.com'})

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event = await session.scalar(select(GovStructure).where(GovStructure.name == 'Government Structure'))
        self.assertIsNone(event)


class TestReceiveGovStructures(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_receiving(self) -> None:
        uuid1 = uuid_pkg.uuid4()
        uuid2 = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid1, name='Government Structure 1',
                                                              email='example@gmail.com'))
            await session.execute(insert(GovStructure).values(uuid=uuid2, name='Government Structure 2',
                                                              email='example@gmail.com'))

        token = AuthJWT().create_access_token(subject=1020, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get('/government-structures/', headers={'Authorization': f'Bearer {token}'})

        expected_result = [
            {'description': None, 'email': 'example@gmail.com',
             'address': None, 'uuid': str(uuid1),
             'name': 'Government Structure 1'},
            {'description': None, 'email': 'example@gmail.com',
             'address': None, 'uuid': str(uuid2),
             'name': 'Government Structure 2'}
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)


class TestReceiveGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_receiving(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='Government Structure',
                                                              email='example@gmail.com'))

        token = AuthJWT().create_access_token(subject=1030, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'/government-structures/{uuid}/',
                                  headers={'Authorization': f'Bearer {token}'})

        expected_result = {'description': None, 'email': 'example@gmail.com',
                           'address': None, 'uuid': str(uuid),
                           'name': 'Government Structure'}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

    async def test_gov_structure_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        token = AuthJWT().create_access_token(subject=1030, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'/government-structures/{uuid}/',
                                  headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            gov_structure = await session.scalar(select(GovStructure).where(GovStructure.uuid == uuid))
        self.assertIsNone(gov_structure)


class TestUpdateGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_updating(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='Government Structure',
                                                              email='example@gmail.com'))

        token = AuthJWT().create_access_token(subject=1030, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.patch(f'/government-structures/{uuid}/',
                                    headers={'Authorization': f'Bearer {token}'},
                                    json={'name': 'Измененное имя'})

        expected_result = {'description': None, 'email': 'example@gmail.com',
                           'address': None, 'uuid': str(uuid),
                           'name': 'Измененное имя'}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

        async with self.Session() as session:
            name = (await session.scalar(select(GovStructure).where(GovStructure.uuid == uuid))).name
        self.assertEqual(name, 'Измененное имя')

    async def test_gov_structure_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        token = AuthJWT().create_access_token(subject=1040, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.patch(f'/government-structures/{uuid}/',
                                    headers={'Authorization': f'Bearer {token}'},
                                    json={'name': 'Измененное имя'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            gov_structure = await session.scalar(select(GovStructure).where(GovStructure.uuid == uuid))
        self.assertIsNone(gov_structure)


class TestDeleteGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_deleting(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='Government Structure',
                                                              email='example@gmail.com'))

        token = AuthJWT().create_access_token(subject=1040, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'/government-structures/{uuid}/',
                                     headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event = await session.scalar(select(GovStructure).where(GovStructure.uuid == uuid))
        self.assertIsNone(event)

    async def test_gov_structure_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        token = AuthJWT().create_access_token(subject=1050, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'/government-structures/{uuid}/',
                                     headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            gov_structure = await session.scalar(select(GovStructure).where(GovStructure.uuid == uuid))
        self.assertIsNone(gov_structure)


class TestSubscribeToGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.gov_structure_uuid = uuid_pkg.uuid4()
        self.user_id = 1060
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=self.gov_structure_uuid, email='example@gmail.com',
                                                              name='Government Structure'))
            await session.execute(insert(User).values({'id': self.user_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))

    async def test_successful_subscribing(self) -> None:
        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'government-structures/{self.gov_structure_uuid}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            gov_structure_sub = await session.scalar(select(GovStructureSubscription).where(
                GovStructureSubscription.gov_structure_uuid == self.gov_structure_uuid,
                GovStructureSubscription.user_id == self.user_id))
        self.assertIsNotNone(gov_structure_sub)

    async def test_the_user_is_already_sub(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=self.gov_structure_uuid,
                                                                          user_id=self.user_id))

        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'government-structures/{self.gov_structure_uuid}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        expected_result = {'detail': [{'loc': ['path', 'uuid'],
                                       'msg': 'you have already subscribed to this government structure',
                                       'type': 'value_error'}]}

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), expected_result)

        async with self.Session() as session:
            gov_structure_sub = await session.scalar(select(GovStructureSubscription).where(
                GovStructureSubscription.gov_structure_uuid == self.gov_structure_uuid,
                GovStructureSubscription.user_id == self.user_id))
        self.assertIsNotNone(gov_structure_sub)

    async def test_gov_structure_doesnt_exist(self) -> None:
        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'government-structures/{uuid_pkg.uuid4()}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)


class TestUnsubscribeFromGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_unsubscribing(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        user_id = 1070
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, email='example@gmail.com',
                                                              name='Government Structure'))
            await session.execute(insert(User).values({'id': user_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=gov_structure_uuid,
                                                                          user_id=user_id))

        token = AuthJWT().create_access_token(subject=user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'government-structures/{gov_structure_uuid}/subscription/',
                                     headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            gov_structure_sub = await session.scalar(select(GovStructureSubscription).where(
                GovStructureSubscription.gov_structure_uuid == gov_structure_uuid,
                GovStructureSubscription.user_id == user_id))
        self.assertIsNone(gov_structure_sub)

    async def test_gov_structure_sub_doesnt_exist(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        user_id = 1080
        token = AuthJWT().create_access_token(subject=user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'government-structures/{gov_structure_uuid}/subscription/',
                                     headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            gov_structure_sub = await session.scalar(select(GovStructureSubscription).where(
                GovStructureSubscription.gov_structure_uuid == gov_structure_uuid,
                GovStructureSubscription.user_id == user_id))
        self.assertIsNone(gov_structure_sub)


class TestReceiveSubscribersToGovStructure(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        user1_id = 1090
        user2_id = 1110
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, email='example@gmail.com',
                                                              name='Government Structure'))
            await session.execute(insert(User).values({'id': user1_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=gov_structure_uuid,
                                                                          user_id=user1_id))
            await session.execute(insert(User).values({'id': user2_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email1@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=gov_structure_uuid,
                                                                          user_id=user2_id))

        token = AuthJWT().create_access_token(subject=1120, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'government-structures/{gov_structure_uuid}/subscribers/',
                                  headers={'Authorization': f'Bearer {token}'})

        expected_result = [
            {
                "first_name": "Имя",
                "last_name": "Фамилия",
                "patronymic": "Отчество",
                "email": "email@email.com",
                "is_government_worker": False
            },
            {
                "first_name": "Имя",
                "last_name": "Фамилия",
                "patronymic": "Отчество",
                "email": "email1@email.com",
                "is_government_worker": False
            }
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

    async def test_gov_structure_doesnt_exist(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        user_id = 1130
        token = AuthJWT().create_access_token(subject=user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'government-structures/{gov_structure_uuid}/subscribers/',
                                  headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            gov_structure_sub = await session.scalar(select(GovStructureSubscription).where(
                GovStructureSubscription.gov_structure_uuid == gov_structure_uuid,
                GovStructureSubscription.user_id == user_id))
        self.assertIsNone(gov_structure_sub)


class TestConfirmEmail(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_confirmation(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        gov_structure = GovStructure(uuid=gov_structure_uuid, name='gov structure', email='example@gmail.com')
        confirmation_uuid = uuid_pkg.uuid4()
        redis_engine.set(f'{confirmation_uuid}-{GovStructure.__name__}', gov_structure.json())

        token = AuthJWT().create_access_token(subject=1131, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'government-structures/email-confirmation/',
                                   headers={'Authorization': f'Bearer {token}'},
                                   json={'confirmation_uuid': str(confirmation_uuid)})

        self.assertEqual(response.status_code, 201)

        expected_result = {'description': None, 'email': 'example@gmail.com',
                           'address': None, 'uuid': str(gov_structure_uuid),
                           'name': 'gov structure'}

        self.assertEqual(response.json(), expected_result)

        async with self.Session() as session:
            gov_structure_in_db = await session.scalar(select(GovStructure).
                                                       where(GovStructure.uuid == gov_structure_uuid))
        self.assertIsNotNone(gov_structure_in_db)

    async def test_gov_structure_is_not_unconfirmed(self) -> None:
        token = AuthJWT().create_access_token(subject=1132, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'government-structures/email-confirmation/',
                                   headers={'Authorization': f'Bearer {token}'},
                                   json={'confirmation_uuid': str(uuid_pkg.uuid4())})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'confirmation_uuid'],
                                                       'msg': 'invalid value',
                                                       'type': 'value_error'}]})
