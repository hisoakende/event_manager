import uuid as uuid_pkg
from typing import Annotated

from asyncpg import ForeignKeyViolationError, UniqueViolationError
from fastapi import APIRouter, status, Depends, HTTPException

from src.dependencies import authorize_user
from src.events.models import EventCreate, Event, EventRead, EventUpdate, EventSubscription
from src.events.service import does_user_is_sub_to_event_by_sub_to_gov_structure, receive_all_subscribers_to_event
from src.gov_structures.models import GovStructure
from src.service import create_model, receive_model, receive_models, update_models, delete_models
from src.users.models import UserRead

events_router = APIRouter(
    prefix='/events',
    tags=['events']
)


@events_router.post('/', status_code=status.HTTP_201_CREATED,
                    dependencies=[Depends(authorize_user(is_government_worker=True))])
async def create_event(event_data: EventCreate) -> EventRead:
    """The view that processes creation the event"""

    event = Event.from_orm(event_data)

    try:
        await create_model(event)
    except ForeignKeyViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'gov_structure_uuid'],
                                     'msg': 'there is no government structure with such a uuid',
                                     'type': 'value_error'}])

    event.gov_structure = await receive_model(GovStructure,  # type: ignore
                                              GovStructure.uuid == event.gov_structure_uuid)  # type: ignore
    return EventRead.from_orm(event)


@events_router.get('/', dependencies=[Depends(authorize_user())])
async def receive_events() -> list[EventRead]:
    """The view that processes getting all events"""

    return [EventRead.from_orm(event) for event in await receive_models(Event)]


@events_router.get('/{uuid}/', dependencies=[Depends(authorize_user())])
async def receive_event() -> EventRead:
    """The view that processes getting the event"""

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return EventRead.from_orm(event)


@events_router.patch('/{uuid}/', dependencies=[Depends(authorize_user(is_government_worker=True))])
async def update_event(uuid: uuid_pkg.UUID, event_changes: EventUpdate) -> EventRead:
    """The view that processes updating the event"""

    try:
        is_updated = await update_models(Event, event_changes, Event.uuid == uuid)  # type: ignore
    except ForeignKeyViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'gov_structure_uuid'],
                                     'msg': 'there is no government structure with such a uuid',
                                     'type': 'value_error'}])

    if not is_updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    return EventRead.from_orm(event)


@events_router.delete('/{uuid}/', status_code=status.HTTP_204_NO_CONTENT,
                      dependencies=[Depends(authorize_user(is_government_worker=True))])
async def delete_event(uuid: uuid_pkg.UUID) -> None:
    """The view that processes deleting the event"""

    is_deleted = await delete_models(Event, Event.uuid == uuid)  # type: ignore
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@events_router.post('/{uuid}/subscription/', status_code=status.HTTP_204_NO_CONTENT)
async def subscribe_to_event(uuid: uuid_pkg.UUID, user_id: Annotated[int, Depends(authorize_user())]) -> None:
    """The view that processes subscribing to the event"""

    subscription = EventSubscription(event_uuid=uuid, user_id=user_id)

    if await does_user_is_sub_to_event_by_sub_to_gov_structure(uuid, user_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['path', 'uuid'],
                                     'msg': 'you have already subscribed to this event',
                                     'type': 'value_error'}])

    try:
        await create_model(subscription)
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['path', 'uuid'],
                                     'msg': 'you have already subscribed to this event',
                                     'type': 'value_error'}])
    except ForeignKeyViolationError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@events_router.delete('/{uuid}/subscription/', status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_event(uuid: uuid_pkg.UUID, user_id: Annotated[int, Depends(authorize_user())]) -> None:
    """The view that processes unsubscribing to the event"""

    is_deleted = await delete_models(EventSubscription,
                                     EventSubscription.event_uuid == uuid,  # type: ignore
                                     EventSubscription.user_id == user_id)  # type: ignore
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@events_router.get('/{uuid}/subscribers/', dependencies=[Depends(authorize_user(is_government_worker=True))])
async def receive_subscribers_to_event(uuid: uuid_pkg.UUID) -> list[UserRead]:
    """The view that processes getting subscribers to the event"""

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    users = await receive_all_subscribers_to_event(uuid, event.gov_structure_uuid)
    return [UserRead.from_orm(user) for user in users]
