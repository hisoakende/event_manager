from typing import Optional

from fastapi_jwt_auth import AuthJWT
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src import database
from src.users import config
from src.users.models import User, RefreshToken


@AuthJWT.load_config
def get_config() -> config.AuthSettings:
    """The function that loads AuthJWT settings"""

    return config.AuthSettings()


async def save_user(user: User) -> Optional[int]:
    """The function that saves the user in database and return his id if he was saved"""

    async with database.Session(expire_on_commit=False) as session:
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            return None

    return user.id


async def get_user_by_email(email: str) -> Optional[User]:
    """The function that returns the user by email from the database"""

    query = select(User).where(User.email == email)
    async with database.Session() as session:
        return await session.scalar(query)


async def save_refresh_token(token: RefreshToken) -> None:
    """The function that saves the refresh token in database"""

    async with database.Session() as session, session.begin():
        session.add(token)
