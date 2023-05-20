import uuid as uuid_pkg
from typing import Annotated

from asyncpg import ForeignKeyViolationError, UniqueViolationError
from fastapi import APIRouter, status, Depends, HTTPException

from src.dependencies import authorize_user
from src.events.models import EventCreate, Event, EventRead, EventUpdate, EventSubscription, EventActivityChangeScheme
from src.events.service import does_user_is_sub_to_event_by_sub_to_gov_structure, receive_subs_to_event_from_db
from src.events.sfp import EventsSFP
from src.gov_structures.models import GovStructure
from src.notifications.celery_ import EmailNotificationsSender
from src.notifications.email_messages import EventChangedEmailMessage, EventCanceledEmailMessage, \
    HostingEventEmailMessage
from src.service import create_model, receive_model, update_models, delete_models, receive_models_by_sfp_or_filter
from src.sfp import UsersSFP
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
async def receive_events(events_sfp: Annotated[EventsSFP, Depends(EventsSFP)]) -> list[EventRead]:
    """The view that processes getting all events"""

    return [EventRead.from_orm(event) for event in await receive_models_by_sfp_or_filter(Event, events_sfp)]


@events_router.get('/{uuid}/', dependencies=[Depends(authorize_user())])
async def receive_event(uuid: uuid_pkg.UUID) -> EventRead:
    """The view that processes getting the event"""

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return EventRead.from_orm(event)


@events_router.patch('/{uuid}/', dependencies=[Depends(authorize_user(is_government_worker=True))])
async def update_event(uuid: uuid_pkg.UUID, event_changes: EventUpdate) -> EventRead:
    """The view that processes updating the event"""

    event_without_changes = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event_without_changes is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        await update_models(Event, event_changes, Event.uuid == uuid)  # type: ignore
    except ForeignKeyViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'gov_structure_uuid'],
                                     'msg': 'there is no government structure with such a uuid',
                                     'type': 'value_error'}])

    event_changes_dict = event_changes.dict(exclude_unset=True)
    event_with_changes = Event(**(event_without_changes.dict() | event_changes_dict))
    event_with_changes.gov_structure = event_without_changes.gov_structure

    event_changes_dict = {k: v for k, v in event_changes_dict.items() if getattr(event_without_changes, k) != v}
    if 'address' in event_changes_dict or 'datetime' in event_changes_dict:
        EmailNotificationsSender.apply_async(
            args=(event_without_changes.json(), EventChangedEmailMessage.__name__),
            kwargs={'is_json': True, 'event_changes': event_changes_dict})

    return EventRead.from_orm(event_with_changes)


@events_router.post('/{uuid}/activity-change/', status_code=status.HTTP_204_NO_CONTENT,
                    dependencies=[Depends(authorize_user(is_government_worker=True))])
async def change_event_activity(uuid: uuid_pkg.UUID, activity_changing: EventActivityChangeScheme) -> None:
    """The view that processes the event activity change"""

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if event.is_active and not activity_changing.is_active:
        EmailNotificationsSender.apply_async(args=(event.json(), EventCanceledEmailMessage.__name__,),
                                             kwargs={'is_json': True})

    elif not event.is_active and activity_changing.is_active:
        EmailNotificationsSender.apply_async(args=(event.json(), HostingEventEmailMessage.__name__,),
                                             kwargs={'is_json': True})

    if event.is_active != activity_changing.is_active:
        await update_models(Event, activity_changing, Event.uuid == uuid)  # type: ignore


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
async def receive_subscribers_to_event(uuid: uuid_pkg.UUID,
                                       users_sfp: Annotated[UsersSFP, Depends(UsersSFP)]) -> list[UserRead]:
    """The view that processes getting subscribers to the event"""

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    users = await receive_subs_to_event_from_db(uuid, event.gov_structure_uuid, users_sfp)
    return [UserRead.from_orm(user) for user in users]
