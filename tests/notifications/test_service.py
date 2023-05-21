import uuid as uuid_pkg
import datetime
from unittest import TestCase
from unittest.mock import patch

from sqlalchemy import insert

from src.events.models import Event
from src.gov_structures.models import GovStructure
from src.notifications.email_messages import EventChangedEmailMessage
from src.notifications.service import receive_events_that_in_few_days_time, receive_events_for_this_and_next_day, \
    get_countdown, schedule_notifications_for_event
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestReceiveEventsThatInFewDaysTime(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        expected_event_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=1)))
            await session.execute(insert(Event).values(uuid=expected_event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=2)))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=3)))

        events = await receive_events_that_in_few_days_time(2, datetime.datetime.now())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].uuid, expected_event_uuid)


class TestReceiveEventsForThisAndNextDay(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        expected_event_uuid1 = uuid_pkg.uuid4()
        expected_event_uuid2 = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=expected_event_uuid1, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(hours=1)))
            await session.execute(insert(Event).values(uuid=expected_event_uuid2, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=1)))
            await session.execute(insert(Event).values(uuid=uuid_pkg.uuid4(), name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime.now() + datetime.timedelta(days=2)))

        events = await receive_events_for_this_and_next_day(datetime.datetime.now())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].uuid, expected_event_uuid1)
        self.assertEqual(events[1].uuid, expected_event_uuid2)


class TestGetCountdown(TestCase):

    def test_start_is_greater_than_end(self) -> None:
        start = datetime.datetime(year=2022, month=1, day=1)
        end = datetime.datetime(year=2020, month=1, day=1)

        expected_result = 0
        result = get_countdown(start, end)
        self.assertEqual(result, expected_result)

    def test_end_is_greater_than_or_equal_to_start(self) -> None:
        start = datetime.datetime(year=2020, month=1, day=1)
        end = datetime.datetime(year=2020, month=1, day=2)

        expected_result = int(datetime.timedelta(days=1).total_seconds())
        result = get_countdown(start, end)
        self.assertEqual(result, expected_result)


class TestScheduleNotificationsForEvent(TestCase):

    def test_scheduling(self) -> None:
        event = Event(uuid=uuid_pkg.uuid4(), gov_structure_uuid=uuid_pkg.uuid4(),
                      datetime=datetime.datetime(year=2020, month=1, day=3))
        with patch('src.notifications.celery_.EmailNotificationsSender.apply_async') as mock:
            schedule_notifications_for_event(event, EventChangedEmailMessage,
                                             datetime.datetime(year=2020, month=1, day=1), datetime.timedelta(days=1))

        self.assertEqual(mock.call_args_list[0].kwargs['args'],
                         (event.uuid, 'EventChangedEmailMessage', event.datetime))
        self.assertEqual(mock.call_args_list[0].kwargs['countdown'], 86400)
