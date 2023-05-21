import datetime
import uuid as uuid_pkg
from unittest.mock import patch

from sqlalchemy import insert, select

from src.events.models import Event, EventSubscription
from src.gov_structures.models import GovStructure
from src.notifications.tasks import EmailNotificationsSender
from src.notifications.email_messages import FiveHoursBeforeEmailMessage
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestSendNotificationEmailNotificationsSender(DBProcessedIsolatedAsyncTestCase):

    async def test_sending(self) -> None:
        event = Event(uuid=uuid_pkg.uuid4(), gov_structure_uuid=uuid_pkg.uuid4(), datetime=datetime.datetime.now())
        user = User(id=100, first_name='аааа', last_name='аааа', patronymic='aaaa',
                    email='example@gmail.com', password='Example123')
        with patch('src.notifications.tasks.send_email') as mock:
            await EmailNotificationsSender(event).send_notification(user, FiveHoursBeforeEmailMessage)

        self.assertTrue(mock.called)


class TestSendNotificationsEmailNotificationsSender(DBProcessedIsolatedAsyncTestCase):

    async def test_sending(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        event_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2020, month=1, day=1)))
            await session.execute(insert(User).values({'id': 111, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(EventSubscription).values(event_uuid=event_uuid,
                                                                   user_id=111))
            await session.execute(insert(User).values({'id': 222, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email1@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(EventSubscription).values(event_uuid=event_uuid,
                                                                   user_id=222))

            event = await session.scalar(select(Event).where(Event.uuid == event_uuid))
        with patch('src.notifications.tasks.EmailNotificationsSender.send_notification') as mock:
            await EmailNotificationsSender(event).send_notifications(FiveHoursBeforeEmailMessage)

        self.assertEqual(mock.call_count, 2)


class TestRunEmailNotificationsSender(DBProcessedIsolatedAsyncTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.event_uuid = uuid_pkg.uuid4()
        gov_structure_uuid = uuid_pkg.uuid4()
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure',
                                                              email='example@gmail.com'))
            await session.execute(insert(Event).values(uuid=self.event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime.datetime(year=2021, month=1, day=1),
                                                       is_active=False))

    def test_event_is_json(self) -> None:
        sender = EmailNotificationsSender()
        event = Event(uuid=uuid_pkg.uuid4(), name='event', gov_structure_uuid=uuid_pkg.uuid4(),
                      datetime_=datetime.datetime.now())
        with patch('src.notifications.tasks.EmailNotificationsSender.send_notifications') as mock:
            sender.run(event.json(), FiveHoursBeforeEmailMessage.__name__, is_json=True)

        self.assertEqual(sender.event, event)

    def test_datetimes_are_different(self) -> None:
        sender = EmailNotificationsSender()
        with patch('src.notifications.tasks.EmailNotificationsSender.send_notifications') as mock:
            sender.run(str(self.event_uuid), FiveHoursBeforeEmailMessage.__name__,
                       datetime_='2020-01-01T00:00:00')

        self.assertFalse(mock.called)

    def test_event_doesnt_exist(self) -> None:
        sender = EmailNotificationsSender()
        with patch('src.notifications.tasks.EmailNotificationsSender.send_notifications') as mock:
            sender.run(str(uuid_pkg.uuid4()), FiveHoursBeforeEmailMessage.__name__)

        self.assertFalse(mock.called)

    def test_event_is_not_active(self) -> None:
        sender = EmailNotificationsSender()
        with patch('src.notifications.tasks.EmailNotificationsSender.send_notifications') as mock:
            sender.run(str(self.event_uuid), FiveHoursBeforeEmailMessage.__name__)

        self.assertFalse(mock.called)
