import uuid as uuid_pkg

from pydantic import EmailStr
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import TEXT, UUID
from sqlmodel import SQLModel, Field

from src.utils import ChangesAreNotEmptyMixin


class GovStructureBase(SQLModel):
    """The model that represents basic government structure fields"""

    name: str
    description: str | None = Field(sa_column=Column(TEXT), default=None)
    address: str | None = None


class GovStructureBaseWithEmail(GovStructureBase):
    """The model that represents basic government structure fields and the email field"""

    email: EmailStr


class GovStructure(GovStructureBaseWithEmail, table=True):
    """
    The model that represents the government structure in the database,
    such as the Ministry of Emergency Situations or the Ministry of Education
    """

    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)


class GovStructureCreate(GovStructureBaseWithEmail):
    """The model that represents the fields needed to create the government structure"""


class GovStructureUpdate(GovStructureBase, ChangesAreNotEmptyMixin):
    """The model that represents the fields needed to change the government structure"""

    name: str | None  # type: ignore


class GovStructureSubscription(SQLModel, table=True):
    """
    The model that represents the subscription to the government structure in the database

    This means that the subscriber automatically subscribes (he will be notified of the events)
    to all events organized by this government structure
    """

    gov_structure_uuid: uuid_pkg.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('govstructure.uuid', ondelete='CASCADE'), primary_key=True))
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), primary_key=True))
