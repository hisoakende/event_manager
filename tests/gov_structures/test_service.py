import uuid as uuid_pkg

from sqlalchemy import insert, text

from src.gov_structures.models import GovStructure, GovStructureSubscription
from src.gov_structures.service import receive_subs_to_gov_structure_from_db
from src.sfp import UsersSFP
from src.users.models import User
from tests.service import DBProcessedIsolatedAsyncTestCase


class TestReceiveSubsToGovStructureFromDb(DBProcessedIsolatedAsyncTestCase):

    async def test_receiving(self) -> None:
        gov_structure_uuid = uuid_pkg.uuid4()
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
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=gov_structure_uuid,
                                                                          user_id=user1_id))
            await session.execute(insert(GovStructureSubscription).values(gov_structure_uuid=gov_structure_uuid,
                                                                          user_id=user2_id))

        expected_result = [user1, user2]
        result = await receive_subs_to_gov_structure_from_db(gov_structure_uuid, UsersSFP(page=0, size=100))
        self.assertEqual(result, expected_result)
