from typing import Optional

from sqlalchemy.exc import IntegrityError

from src import database
from src.auth.models import User


async def save_user(user: User) -> Optional[int]:
    """The function that saves user in database and return his id if he was saved"""

    async with database.Session(expire_on_commit=False) as session:
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            return None

    return user.id
