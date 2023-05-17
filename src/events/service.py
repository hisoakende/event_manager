import uuid as uuid_pkg

from sqlalchemy import select, union
from sqlalchemy.orm import noload
from sqlalchemy.sql import CompoundSelect

from src.events.models import Event, EventSubscription
from src.gov_structures.models import GovStructureSubscription
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


def create_receiving_subs_to_event_union_query_from_db(event_uuid: uuid_pkg.UUID,
                                                       gov_structure_uuid: uuid_pkg.UUID) -> CompoundSelect:
    """
    The function that returns the request to receive users who are subscribed to the event,
    including those who are subscribed to the government structure that hosts this event
    """

    event_subs_query = select(User) \
        .join(EventSubscription, EventSubscription.user_id == User.id) \
        .where(EventSubscription.event_uuid == event_uuid)

    gov_structure_subs_query = select(User) \
        .join(GovStructureSubscription, GovStructureSubscription.user_id == User.id) \
        .where(GovStructureSubscription.gov_structure_uuid == gov_structure_uuid)

    return union(event_subs_query, gov_structure_subs_query)


async def receive_subs_to_event_from_db(event_uuid: uuid_pkg.UUID,
                                        gov_structure_uuid: uuid_pkg.UUID,
                                        users_sfp: SortingFilteringPaging | None = None) -> list[UserRead]:
    """
    The function that returns the list of all users who are subscribed to the event,
    including those who are subscribed to the government structure that hosts this event
    """

    query = create_receiving_subs_to_event_union_query_from_db(event_uuid, gov_structure_uuid)

    if users_sfp is not None:
        query = users_sfp.paginate(query)
        query = users_sfp.sort(users_sfp.filter(query))  # type: ignore

    query = select(User).from_statement(query)
    return (await execute_db_query(query)).scalars().fetchall()
