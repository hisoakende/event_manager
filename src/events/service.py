import uuid as uuid_pkg

from sqlalchemy import select, union

from src.events.models import Event, EventSubscription
from src.gov_structures.models import GovStructureSubscription, GovStructure
from src.service import execute_db_query
from src.users.models import UserRead, User


async def does_user_is_sub_to_event_by_sub_to_gov_structure(event_uuid: uuid_pkg.UUID,
                                                            user_id: int) -> bool:
    """
    The function that checks the subscription to the event by subscribing
    to the government structure that hosts this event
    """

    query = select(GovStructureSubscription) \
        .join(GovStructure, GovStructure.uuid == GovStructureSubscription.gov_structure_uuid) \
        .join(Event, Event.gov_structure_uuid == GovStructure.uuid) \
        .where(GovStructureSubscription.user_id == user_id,
               Event.uuid == event_uuid)
    return bool((await execute_db_query(query)).scalar())


async def receive_all_subscribers_to_event(event_uuid: uuid_pkg.UUID,
                                           gov_structure_uuid: uuid_pkg.UUID) -> list[UserRead]:
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

    query = select(User).from_statement(union(event_subs_query, gov_structure_subs_query))
    return (await execute_db_query(query)).scalars().fetchall()