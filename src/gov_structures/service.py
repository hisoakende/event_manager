import uuid as uuid_pkg

from sqlmodel import select

from src.gov_structures.models import GovStructureSubscription
from src.service import execute_db_query
from src.users.models import User


async def receive_subs_to_gov_structure_from_db(gov_structure_uuid: uuid_pkg.UUID) -> list[User]:
    """The function that executes the query to get subscribers to the government structure"""

    query = select(User) \
        .join(GovStructureSubscription, GovStructureSubscription.user_id == User.id) \
        .where(GovStructureSubscription.gov_structure_uuid == gov_structure_uuid)
    return (await execute_db_query(query)).scalars().fetchall()
