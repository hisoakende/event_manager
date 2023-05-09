from typing import Any, TypeVar

from sqlalchemy import select, update, delete
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


SQLModelSubClass = TypeVar('SQLModelSubClass', bound=SQLModel)


async def create_model(model: SQLModelSubClass) -> bool:
    """The function that creates model"""

    async with database.Session() as session:
        session.add(model)
        try:
            await session.commit()
        except IntegrityError:
            return False

    return True


async def receive_models(model_type: type[SQLModelSubClass]) -> list[SQLModelSubClass]:
    """The function that returns all models of the given model type"""

    query = select(model_type)
    return (await execute_db_query(query)).scalars().fetchall()


async def receive_model(model_type: type[SQLModelSubClass], *conditions: BinaryExpression) -> SQLModelSubClass | None:
    """The function that returns the model by id from the database"""

    query = select(model_type).where(*conditions)
    return (await execute_db_query(query)).scalar()


async def update_model(model_type: type[SQLModelSubClass], data: SQLModel, *conditions: BinaryExpression) -> bool:
    """The function that updates model"""

    query = update(model_type).values(data.dict(exclude_none=True)).where(*conditions)
    try:
        await execute_db_query(query)
    except IntegrityError:
        return False

    return True


async def delete_model(model_type: type[SQLModelSubClass], *conditions: BinaryExpression) -> None:
    """The function that deletes the model from the database"""

    query = delete(model_type).where(*conditions)
    await execute_db_query(query)


def is_user_in_blacklist(user_id: int) -> bool:
    """The function that checks if the user is blacklisted"""

    return redis_engine.sismember(config.USERS_BLACKLIST_NAME, user_id)
