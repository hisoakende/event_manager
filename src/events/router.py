from asyncpg import ForeignKeyViolationError
from fastapi import APIRouter, status, Depends, HTTPException

from src.dependencies import authorize_user
from src.events.models import EventCreate, Event, EventRead
from src.gov_structures.models import GovStructure
from src.service import create_model, receive_model, receive_models

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

    return [EventRead.from_orm(event) for event in await receive_models(EventRead)]


@events_router.get('/{uuid}/', dependencies=[Depends(authorize_user())])
async def receive_event() -> EventRead:
    """The view that processes getting the event"""

    event = await receive_model(Event, Event.uuid == uuid)  # type: ignore
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return EventRead.from_orm(event)
