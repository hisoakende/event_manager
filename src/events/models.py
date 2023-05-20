import datetime as datetime_pkg
import uuid as uuid_pkg

from pydantic import BaseModel
from sqlalchemy import Column, TEXT, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import SQLModel, Field, Relationship

from src.gov_structures.models import GovStructure
from src.utils import ChangesAreNotEmptyMixin


class EventBase(SQLModel):
    """The model that represents basic event fields"""

    name: str
    description: str | None = Field(sa_column=Column(TEXT), default=None)
    address: str | None = None
    datetime: datetime_pkg.datetime


class EventBaseWithGovStructureUUID(EventBase):
    """The model that represents basic event fields and the government structure uuid field"""

    gov_structure_uuid: uuid_pkg.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('govstructure.uuid', ondelete='CASCADE'), nullable=False))


class EventBaseWithUUID(EventBase):
    """The model that represents basic event fields and the uuid field"""

    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)


class Event(EventBaseWithUUID, EventBaseWithGovStructureUUID, table=True):
    """The model that represents the event in the database"""

    gov_structure: GovStructure = Relationship(
        sa_relationship_kwargs={'primaryjoin': 'Event.gov_structure_uuid == GovStructure.uuid',
                                'lazy': 'joined'})
    is_active: bool = True


class EventCreate(EventBaseWithGovStructureUUID):
    """The model that represents the fields needed to create the event"""


class EventRead(EventBaseWithUUID):
    """The model that represents the fields which will be returned by API"""

    gov_structure: GovStructure
    is_active: bool = True


class EventUpdate(EventBase, ChangesAreNotEmptyMixin):
    """The model that represents the fields needed to change the government structure"""

    name: str | None = None  # type: ignore
    datetime: datetime_pkg.datetime | None = None  # type: ignore


class EventActivityChangeScheme(BaseModel):
    """The schema that is needed to change the activity of the event"""

    is_active: bool


class EventSubscription(SQLModel, table=True):
    """The model that represents the subscription to the event in the database"""

    event_uuid: uuid_pkg.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('event.uuid', ondelete='CASCADE'), primary_key=True))
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), primary_key=True))
