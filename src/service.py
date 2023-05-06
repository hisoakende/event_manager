from typing import Any

from sqlalchemy import update
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import SQLModel

from src import database, config
from src.redis_ import redis_engine


async def execute_db_query(query: Any) -> Result:
    """The function that executes the given query to db"""

    async with database.Session() as session, session.begin():
        return await session.execute(query)


async def update_model(model_type: type[SQLModel], data: SQLModel, condition: BinaryExpression) -> bool:
    """The function that updates model"""

    query = update(model_type).values(data.dict(exclude_none=True)).where(condition)
    try:
        await execute_db_query(query)
    except IntegrityError:
        return False
    return True


def is_user_in_black_list(user_id: int) -> bool:
    """The function that checks if the user is blacklisted"""

    return redis_engine.sismember(config.USERS_BLACKLIST_NAME, user_id)
