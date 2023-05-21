import datetime
import uuid as uuid_pkg
from unittest.mock import patch

from sqlalchemy import insert

from src.events.models import Event
from src.gov_structures.models import GovStructure
from src.notifications.celery_ import schedule_notifications, schedule_notifications_on_start_up
from tests.service import DBProcessedIsolatedAsyncTestCase


class ScheduleNotifications(DBProcessedIsolatedAsyncTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        gov_structure_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=7)))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=1)))

    def test_scheduling(self):
        with patch('src.notifications.celery_.schedule_notifications_for_event') as mock:
            schedule_notifications()

        self.assertEqual(mock.call_count, 3)
        self.assertEqual(mock.mock_calls[0].args[3], datetime.timedelta(days=7))
        self.assertEqual(mock.mock_calls[1].args[3], datetime.timedelta(days=1))
        self.assertEqual(mock.mock_calls[2].args[3], datetime.timedelta(hours=5))


class TestScheduleNotificationsOnStartUp(DBProcessedIsolatedAsyncTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        gov_structure_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now()))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=1)))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=3)))

    def test_scheduling(self) -> None:
        with patch('src.notifications.celery_.schedule_notifications_for_event') as mock:
            schedule_notifications_on_start_up()

        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.mock_calls[0].args[3], datetime.timedelta(days=1))
        self.assertEqual(mock.mock_calls[1].args[3], datetime.timedelta(hours=5))
