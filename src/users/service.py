from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from src import database, config
from src.redis_ import redis_engine
from src.service import execute_db_query
from src.users.models import User


async def save_user(user: User) -> int | None:
    """The function that saves the user in database and return his id if he was saved"""

    async with database.Session() as session:
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            return None

    return user.id


async def get_user_by_email(email: str) -> User | None:
    """The function that returns the user by email from the database"""

    query = select(User).where(User.email == email)
    return (await execute_db_query(query)).scalar()


async def get_user_by_id(user_id: int) -> User | None:
    """The function that returns the user by id from the database"""

    query = select(User).where(User.id == user_id)
    return (await execute_db_query(query)).scalar()


async def delete_user_from_db(user_id: int) -> None:
    """The function that deletes the user by id from the database"""

    query = delete(User).where(User.id == user_id)
    await execute_db_query(query)


def add_user_to_blacklist(user_id: int) -> None:
    """
    The function that adds user to the blacklist

    This is necessary so that in the interval between the removal of the user
    and the expiration of the last access token, he could not make requests
    """

    redis_engine.sadd(config.USERS_BLACKLIST_NAME, user_id)
