import datetime as datetime_pkg
import uuid as uuid_pkg

from sqlalchemy import Column, TEXT, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import SQLModel, Field, Relationship

from src.gov_structures.models import GovStructure


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


class EventCreate(EventBaseWithGovStructureUUID):
    """The model that represents the fields needed to create the event"""


class EventRead(EventBaseWithUUID):
    """The model that represents the fields which will be returned by API"""

    gov_structure: GovStructure


class EventUpdate(EventBase):
    """The model that represents the fields needed to change the government structure"""

    name: str | None = None  # type: ignore
    gov_structure_uuid: uuid_pkg.UUID | None = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('govstructure.uuid', ondelete='CASCADE')), default=None)
