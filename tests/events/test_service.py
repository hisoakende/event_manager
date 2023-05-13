import datetime
import uuid as uuid_pkg

from sqlalchemy import insert, delete, text

from src.events.models import Event, EventSubscription
from src.events.service import does_user_is_sub_to_event_by_sub_to_gov_structure, receive_subs_to_event_from_db
from src.gov_structures.models import GovStructure, GovStructureSubscription
from src.sfp import UsersSFP
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestDoesUserIsSubToEventBySubToGovStructure(DBProcessedIsolatedAsyncTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.gov_structure_uuid = uuid_pkg.uuid4()
        self.event_uuid = uuid_pkg.uuid4()
        self.datetime_ = datetime.datetime(year=2020, month=1, day=1)
        self.user_id = 1110
        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=self.gov_structure_uuid, name='gov structure'))
            await session.execute(insert(Event).values(uuid=self.event_uuid, name='event',
                                                       gov_structure_uuid=self.gov_structure_uuid,
                                                       datetime=self.datetime_))
            await session.execute(insert(User).values({'id': self.user_id, 'first_name': 'Имя', 'last_name': 'Фамилия',
                                                       'patronymic': 'Отчество', 'email': 'email@email.com',
                                                       'password': 'Password123'}))
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=self.gov_structure_uuid,
                                                                          user_id=self.user_id))

    async def test_user_is_sub_to_gov_structure(self) -> None:
        expected_result = True
        result = await does_user_is_sub_to_event_by_sub_to_gov_structure(self.event_uuid, self.user_id)
        self.assertEqual(result, expected_result)

    async def test_user_is_not_sub_to_gov_structure(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(delete(GovStructureSubscription).where(
                GovStructureSubscription.gov_structure_uuid == self.gov_structure_uuid))

        expected_result = False
        result = await does_user_is_sub_to_event_by_sub_to_gov_structure(self.event_uuid, self.user_id)
        self.assertEqual(result, expected_result)

    async def test_event_doesnt_exist(self) -> None:
        async with self.Session() as session, session.begin():
            await session.execute(delete(Event).where(Event.uuid == self.event_uuid))

        expected_result = False
        result = await does_user_is_sub_to_event_by_sub_to_gov_structure(self.event_uuid, self.user_id)
        self.assertEqual(result, expected_result)


class TestReceiveSubsToEventFromDb(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
        event_uuid = uuid_pkg.uuid4()
        datetime_ = datetime.datetime(year=2020, month=1, day=1)
        user1 = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                     email='email@email.com', password='Password123')
        user2 = User(first_name='Имя', last_name='Фамилия', patronymic='Отчество',
                     email='email1@email.com', password='Password123')
        async with self.Session() as session, session.begin():
            user1_id = await session.scalar(text("SELECT nextval('user_id_seq')")) + 1
            user2_id = user1_id + 1
            session.add(user1)
            session.add(user2)

        async with self.Session() as session, session.begin():
            await session.execute(insert(GovStructure).values(uuid=gov_structure_uuid, name='gov structure'))
            await session.execute(insert(Event).values(uuid=event_uuid, name='event',
                                                       gov_structure_uuid=gov_structure_uuid,
                                                       datetime=datetime_))
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=gov_structure_uuid,
                                                                          user_id=user1_id))
            await session.execute(insert(EventSubscription).values(event_uuid=event_uuid,
                                                                   user_id=user2_id))

        expected_result = [user2, user1]
        result = await receive_subs_to_event_from_db(event_uuid, gov_structure_uuid, UsersSFP(page=0, size=100))
        self.assertEqual(result, expected_result)
