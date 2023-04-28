from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """A model that represents an ordinary citizen or a government worker"""

    id: int = Field(primary_key=True)
    first_name: str
    last_name: str
    patronymic: str
    email: str = Field(unique=True)
    password: str
    is_government_worker: bool
