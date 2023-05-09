import uuid as uuid_pkg

from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT
from sqlmodel import SQLModel, Field

from src.utils import ChangesAreNotEmptyMixin


class GovStructureBase(SQLModel):
    """The model that represents basic government structure fields"""

    name: str
    description: str | None = Field(sa_column=Column(TEXT), default=None)
    email: EmailStr | None = None
    address: str | None = None


class GovStructure(GovStructureBase, table=True):
    """
    The model that represents the government structure,
    such as the Ministry of Emergency Situations or the Ministry of Education
    """

    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)


class GovStructureCreate(GovStructureBase):
    """The model that represents the fields needed to create the government structure"""


class GovStructureUpdate(GovStructureBase, ChangesAreNotEmptyMixin):
    """The model that represents the fields needed to change the government structure"""

    name: str | None
