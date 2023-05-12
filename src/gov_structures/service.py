import uuid as uuid_pkg

from sqlmodel import select

from src.gov_structures.models import GovStructureSubscription
from src.service import execute_db_query
from src.sfp import SortingFilteringPaging
from src.users.models import User


async def receive_subs_to_gov_structure_from_db(gov_structure_uuid: uuid_pkg.UUID,
                                                users_sfp: SortingFilteringPaging) -> list[User]:
    """The function that executes the query to get subscribers to the government structure"""

    query = select(User) \
        .join(GovStructureSubscription, GovStructureSubscription.user_id == User.id) \
        .where(GovStructureSubscription.gov_structure_uuid == gov_structure_uuid)

    query = users_sfp.sort(users_sfp.filter(query))
    query = users_sfp.paginate(query)
    return (await execute_db_query(query)).scalars().fetchall()
