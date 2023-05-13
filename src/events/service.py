import uuid as uuid_pkg

from sqlalchemy import select, union
from sqlalchemy.orm import noload, lazyload

from src.events.models import Event, EventSubscription
from src.gov_structures.models import GovStructureSubscription, GovStructure
from src.service import execute_db_query
from src.sfp import SortingFilteringPaging
from src.users.models import UserRead, User


async def does_user_is_sub_to_event_by_sub_to_gov_structure(event_uuid: uuid_pkg.UUID,
                                                            user_id: int) -> bool:
    """
    The function that checks the subscription to the event by subscribing
    to the government structure that hosts this event
    """

    event_query = select(Event).where(Event.uuid == event_uuid).options(noload(Event.gov_structure))
    event = (await execute_db_query(event_query)).scalar()

    if event is None:
        return False

    gov_structure_sub_query = select(GovStructureSubscription).where(
        GovStructureSubscription.gov_structure_uuid == event.gov_structure_uuid,
        GovStructureSubscription.user_id == user_id
    )
    gov_structure_sub = (await execute_db_query(gov_structure_sub_query)).scalar()

    return gov_structure_sub is not None


async def receive_subs_to_event_from_db(event_uuid: uuid_pkg.UUID,
                                        gov_structure_uuid: uuid_pkg.UUID,
                                        users_sfp: SortingFilteringPaging) -> list[UserRead]:
    """
    The function that returns the list of all users who are subscribed to the event,
    including those who are subscribed to the government structure that hosts this event
    """

    event_subs_query = select(User) \
        .join(EventSubscription, EventSubscription.user_id == User.id) \
        .where(EventSubscription.event_uuid == event_uuid)

    gov_structure_subs_query = select(User) \
        .join(GovStructureSubscription, GovStructureSubscription.user_id == User.id) \
        .where(GovStructureSubscription.gov_structure_uuid == gov_structure_uuid)

    query = users_sfp.paginate(union(event_subs_query, gov_structure_subs_query))
    query = users_sfp.sort(users_sfp.filter(query))
    query = select(User).from_statement(query)
    return (await execute_db_query(query)).scalars().fetchall()
