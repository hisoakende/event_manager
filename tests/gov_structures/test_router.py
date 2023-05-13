import uuid as uuid_pkg

from fastapi_jwt_auth import AuthJWT
from sqlalchemy import select, insert
from starlette.testclient import TestClient

from src.gov_structures.models import GovStructure, GovStructureSubscription
from src.main import app
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestCreateGovStructure(DBProcessedIsolatedAsyncTestCase):

    async def test_creating(self) -> None:
        token = AuthJWT().create_access_token(subject=1010, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post('/government-structures/',
                                   headers={'Authorization': f'Bearer {token}'},
                                   json={'name': 'Government Structure'})

        expected_result = {'description': None, 'email': None,
                           'address': None, 'name': 'Government Structure'}
        result = response.json()
        result.pop('uuid')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(result, expected_result)

        async with self.Session() as session:
            event = await session.scalar(select(GovStructure).where(GovStructure.name == 'Government Structure'))
        self.assertIsNotNone(event)


class TestReceiveGovStructures(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        uuid1 = uuid_pkg.uuid4()
        uuid2 = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid1, name='Government Structure 1'))
            await session.execute(insert(GovStructure).values(uuid=uuid2, name='Government Structure 2'))

        token = AuthJWT().create_access_token(subject=1020, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get('/government-structures/', headers={'Authorization': f'Bearer {token}'})

        expected_result = [
            {'description': None, 'email': None,
             'address': None, 'uuid': str(uuid1),
             'name': 'Government Structure 1'},
            {'description': None, 'email': None,
             'address': None, 'uuid': str(uuid2),
             'name': 'Government Structure 2'}
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)


class TestReceiveGovStructure(DBProcessedIsolatedAsyncTestCase):

    async def test_successful_receiving(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='Government Structure'))

        token = AuthJWT().create_access_token(subject=1030, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'/government-structures/{uuid}/',
                                  headers={'Authorization': f'Bearer {token}'})

        expected_result = {'description': None, 'email': None,
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

    async def test_successful_updating(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='Government Structure'))

        token = AuthJWT().create_access_token(subject=1030, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.patch(f'/government-structures/{uuid}/',
                                    headers={'Authorization': f'Bearer {token}'},
                                    json={'name': 'Измененное имя'})

        expected_result = {'description': None, 'email': None,
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

    async def test_successful_deleting(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='Government Structure'))

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

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.gov_structure_uuid = uuid_pkg.uuid4()
        self.user_id = 1060
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=self.gov_structure_uuid,
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

    async def test_successful_unsubscribing(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        user_id = 1070
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid,
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

    async def test_successful_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        user1_id = 1090
        user2_id = 1110
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid,
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
