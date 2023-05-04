from sqlmodel import SQLModel, Field


class RefreshToken(SQLModel, table=True):
    """The model that represents the refresh token"""

    user_id: int = Field(primary_key=True, foreign_key='user.id')
    value: str = Field(primary_key=True)


class TokensResponseModel(SQLModel):
    """The models that represents the schema of the response with tokens"""

    access_token: str
    refresh_token: str
