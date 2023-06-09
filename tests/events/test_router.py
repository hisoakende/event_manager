import datetime
import uuid as uuid_pkg
from unittest.mock import patch

from fastapi_jwt_auth import AuthJWT
from sqlalchemy import insert, select, delete, update
from starlette.testclient import TestClient

from src.events.models import Event, EventSubscription
from src.gov_structures.models import GovStructure, GovStructureSubscription
from src.main import app
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestCreateEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    def setUp(self) -> None:
        self.token = AuthJWT().create_access_token(subject=100, user_claims={'is_government_worker': True})

    async def test_successful_creating(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='gov structure',
                                                              email='example@gmail.com'))

        with TestClient(app=app) as client:
            response = client.post('/events/', headers={'Authorization': f'Bearer {self.token}'},
                                   json={'name': 'event',
                                         'datetime': '2020-01-01T00:00:00',
                                         'gov_structure_uuid': str(uuid)})

        expected_result = {
            'is_active': True,
            'name': 'event',
            'description': None,
            'address': None,
            'datetime': '2020-01-01T00:00:00',
            'gov_structure': {
                'name': 'gov structure',
                'description': None,
                'email': 'example@gmail.com',
                'address': None,
                'uuid': str(uuid)
            }
        }

        result = response.json()
        event_uuid = result.pop('uuid')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(result, expected_result)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == event_uuid))
        self.assertIsNotNone(event)

    async def test_defunct_government_structure(self) -> None:
        with TestClient(app=app) as client:
            response = client.post('/events/',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   json={'name': 'event',
                                         'datetime': '2020-01-01T00:00:00',
                                         'gov_structure_uuid': 'edcd54ea-1a50-46cf-b207-8d40d2357887'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['body', 'gov_structure_uuid'],
                                                       'msg': 'there is no government structure with such a uuid',
                                                       'type': 'value_error'}]})


class TestReceiveEvents(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_receiving(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event 1',
                                                       gov_structure_uuid=uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event 2',
                                                       gov_structure_uuid=uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))

        token = AuthJWT().create_access_token(subject=200, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get('/events/', headers={'Authorization': f'Bearer {token}'})

        expected_result = [
            {
                'is_active': True,
                'name': 'event 1',
                'description': None,
                'address': None,
                'datetime': '2020-01-01T00:00:00',
                'gov_structure': {
                    'name': 'gov structure',
                    'description': None,
                    'email': 'example@gmail.com',
                    'address': None,
                    'uuid': str(uuid)
                }
            },
            {
                'is_active': True,
                'name': 'event 2',
                'description': None,
                'address': None,
                'datetime': '2020-01-01T00:00:00',
                'gov_structure': {
                    'name': 'gov structure',
                    'description': None,
                    'email': 'example@gmail.com',
                    'address': None,
                    'uuid': str(uuid)
                }
            }
        ]

        result = response.json()
        result[0].pop('uuid')
        result[1].pop('uuid')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, expected_result)


class TestReceiveEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    def setUp(self) -> None:
        self.token = AuthJWT().create_access_token(subject=250, user_claims={'is_government_worker': True})

    async def test_event_exist(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        event_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))

        with TestClient(app=app) as client:
            response = client.get(f'/events/{event_uuid}/', headers={'Authorization': f'Bearer {self.token}'})

        expected_result = {
            'is_active': True,
            'name': 'event',
            'description': None,
            'address': None,
            'datetime': '2020-01-01T00:00:00',
            'uuid': str(event_uuid),
            'gov_structure': {
                'name': 'gov structure',
                'description': None,
                'email': 'example@gmail.com',
                'address': None,
                'uuid': str(gov_structure_uuid)
            }
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

    async def test_event_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        with TestClient(app=app) as client:
            response = client.get(f'/events/{uuid}/', headers={'Authorization': f'Bearer {self.token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == uuid))
        self.assertIsNone(event)


class TestUpdateEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.token = AuthJWT().create_access_token(subject=300, user_claims={'is_government_worker': True})
        self.gov_structure_uuid = uuid_pkg.uuid4()
        self.event_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=self.gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=self.event_uuid, name='event',
                                                       gov_structure_uuid=self.gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))

    async def test_successful_updating(self) -> None:
        with TestClient(app=app) as client:
            response = client.patch(f'/events/{self.event_uuid}/', headers={'Authorization': f'Bearer {self.token}'},
                                    json={'name': 'Измененное имя'})

        expected_result = {
            'is_active': True,
            'name': 'Измененное имя',
            'description': None,
            'address': None,
            'datetime': '2020-01-01T00:00:00',
            'uuid': str(self.event_uuid),
            'gov_structure': {
                'name': 'gov structure',
                'description': None,
                'email': 'example@gmail.com',
                'address': None,
                'uuid': str(self.gov_structure_uuid)
            }
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

        event_name_expected = 'Измененное имя'
        async with self.Session() as session:
            event_name = (await session.scalar(select(Event).where(Event.uuid == self.event_uuid))).name
        self.assertEqual(event_name, event_name_expected)

    async def test_updating_datetime(self) -> None:
        with patch('src.events.router.EmailNotificationsSender.apply_async') as mock, \
                TestClient(app=app) as client:
            response = client.patch(f'/events/{self.event_uuid}/', headers={'Authorization': f'Bearer {self.token}'},
                                    json={'datetime': '2020-03-01T00:00:00'})

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 200)

    async def test_updating_address(self) -> None:
        with patch('src.events.router.EmailNotificationsSender.apply_async') as mock, \
                TestClient(app=app) as client:
            response = client.patch(f'/events/{self.event_uuid}/', headers={'Authorization': f'Bearer {self.token}'},
                                    json={'datetime': '2020-03-01T00:00:00'})

        self.assertTrue(mock.called)
        self.assertEqual(response.status_code, 200)

    async def test_event_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        with TestClient(app=app) as client:
            response = client.patch(f'/events/{uuid}/', headers={'Authorization': f'Bearer {self.token}'},
                                    json={'name': 'Измененное имя'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == uuid))
        self.assertIsNone(event)


class TestChangeEventActivity(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.token = AuthJWT().create_access_token(subject=404, user_claims={'is_government_worker': True})
        self.gov_structure_uuid = uuid_pkg.uuid4()
        self.event_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=self.gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=self.event_uuid, name='event',
                                                       gov_structure_uuid=self.gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))

    async def test_change_false_to_true(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(update(Event).values(is_active=False).where(Event.uuid == self.event_uuid))

        with patch('src.events.router.EmailNotificationsSender.apply_async') as mock, TestClient(app=app) as client:
            response = client.post(f'/events/{self.event_uuid}/activity-change/',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   json={'is_active': True})

        self.assertIn('HostingEventEmailMessage', mock.call_args_list[0].kwargs['args'])
        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event_activity = (await session.scalar(select(Event).where(Event.uuid == self.event_uuid))).is_active
        self.assertTrue(event_activity)

    async def test_change_true_to_false(self) -> None:
        with patch('src.events.router.EmailNotificationsSender.apply_async') as mock, TestClient(app=app) as client:
            response = client.post(f'/events/{self.event_uuid}/activity-change/',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   json={'is_active': False})

        self.assertIn('EventCanceledEmailMessage', mock.call_args_list[0].kwargs['args'])
        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event_activity = (await session.scalar(select(Event).where(Event.uuid == self.event_uuid))).is_active
        self.assertFalse(event_activity)

    async def test_activity_does_not_change(self) -> None:
        with TestClient(app=app) as client:
            response = client.post(f'/events/{self.event_uuid}/activity-change/',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   json={'is_active': True})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event_activity = (await session.scalar(select(Event).where(Event.uuid == self.event_uuid))).is_active
        self.assertTrue(event_activity)

    async def test_event_does_not_exist(self) -> None:
        with TestClient(app=app) as client:
            response = client.post(f'/events/{uuid_pkg.uuid4()}/activity-change/',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   json={'is_active': False})

        self.assertEqual(response.status_code, 404)


class TestDeleteEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_deleting(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        event_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))

        token = AuthJWT().create_access_token(subject=450, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'/events/{event_uuid}/', headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == event_uuid))
        self.assertIsNone(event)

    async def test_event_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        token = AuthJWT().create_access_token(subject=500, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'/events/{uuid}/', headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == uuid))
        self.assertIsNone(event)


class TestSubscribeToEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.gov_structure_uuid = uuid_pkg.uuid4()
        self.event_uuid = uuid_pkg.uuid4()
        self.user_id = 550
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=self.gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=self.event_uuid, name='event',
                                                       gov_structure_uuid=self.gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))
            await session.execute(insert(User).values({'id': self.user_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))

    async def test_successful_subscribing(self) -> None:
        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'/events/{self.event_uuid}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event = await session.scalar(
                select(EventSubscription).where(EventSubscription.event_uuid == self.event_uuid))
        self.assertIsNotNone(event)

    async def test_user_is_sub_to_gov_structure(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=self.gov_structure_uuid,
                                                                          user_id=self.user_id))

        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'/events/{self.event_uuid}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['path', 'uuid'],
                                                       'msg': 'you have already subscribed to this event',
                                                       'type': 'value_error'}]})

    async def test_user_is_sub_to_event(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(insert(EventSubscription).values(event_uuid=self.event_uuid,
                                                                   user_id=self.user_id))

        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'/events/{self.event_uuid}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail': [{'loc': ['path', 'uuid'],
                                                       'msg': 'you have already subscribed to this event',
                                                       'type': 'value_error'}]})

    async def test_event_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(delete(Event).where(Event.uuid == self.event_uuid))

        token = AuthJWT().create_access_token(subject=self.user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.post(f'/events/{uuid}/subscription/',
                                   headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == uuid))
        self.assertIsNone(event)


class TestUnsubscribeFromEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_deleting(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        event_uuid = uuid_pkg.uuid4()
        user_id = 600
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))
            await session.execute(insert(User).values({'id': user_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(EventSubscription).values(event_uuid=event_uuid,
                                                                   user_id=user_id))

        token = AuthJWT().create_access_token(subject=user_id, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'/events/{event_uuid}/subscription/',
                                     headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 204)

        async with self.Session() as session:
            event = await session.scalar(select(EventSubscription).where(EventSubscription.event_uuid == event_uuid))
        self.assertIsNone(event)

    async def test_event_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        token = AuthJWT().create_access_token(subject=650, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.delete(f'/events/{uuid}/subscription/',
                                     headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == uuid))
        self.assertIsNone(event)


class TestReceiveSubscribersToEvent(DBProcessedIsolatedAsyncTestCase):
    test_endpoint = True

    async def test_successful_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        event_uuid = uuid_pkg.uuid4()
        user1_id = 700
        user2_id = 750
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))
            await session.execute(insert(User).values({'id': user1_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(EventSubscription).values(event_uuid=event_uuid,
                                                                   user_id=user1_id))
            await session.execute(insert(User).values({'id': user2_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email1@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(EventSubscription).values(event_uuid=event_uuid,
                                                                   user_id=user2_id))

        token = AuthJWT().create_access_token(subject=800, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'/events/{event_uuid}/subscribers/',
                                  headers={'Authorization': f'Bearer {token}'})

        expected_result = [
            {
                "first_name": "Имя",
                "last_name": "Фамилия",
                "patronymic": "Отчество",
                "email": "email1@email.com",
                "is_government_worker": False
            },
            {
                "first_name": "Имя",
                "last_name": "Фамилия",
                "patronymic": "Отчество",
                "email": "email@email.com",
                "is_government_worker": False
            }
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

    async def test_event_doesnt_exist(self) -> None:
        uuid = uuid_pkg.uuid4()
        token = AuthJWT().create_access_token(subject=800, user_claims={'is_government_worker': True})
        with TestClient(app=app) as client:
            response = client.get(f'/events/{uuid}/subscribers/',
                                  headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 404)

        async with self.Session() as session:
            event = await session.scalar(select(Event).where(Event.uuid == uuid))
        self.assertIsNone(event)
