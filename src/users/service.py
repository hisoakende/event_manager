from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.selectable import Select

from src import database
from src.service import execute_db_query
from src.users.models import User


async def save_user(user: User) -> Optional[int]:
    """The function that saves the user in database and return his id if he was saved"""

    async with database.Session() as session:
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            return None

    return user.id


async def get_user_by_email(email: str) -> Optional[User]:
    """The function that returns the user by email from the database"""

    query = select(User).where(User.email == email)
    return (await execute_db_query(query)).scalar()
