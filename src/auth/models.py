from sqlalchemy import ForeignKey, Column, Integer
from sqlmodel import SQLModel, Field


class RefreshToken(SQLModel, table=True):
    """The model that represents the refresh token"""

    user_id: int = Field(sa_column=Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), primary_key=True))
    value: str = Field(primary_key=True)


class TokensResponseModel(SQLModel):
    """The models that represents the schema of the response with tokens"""

    access_token: str
    refresh_token: str
