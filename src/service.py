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


async def create_model(model: SQLModelSubClass) -> None:
    """The function that creates model"""

    async with database.Session() as session:
        session.add(model)
        try:
            await session.commit()
        except IntegrityError as e:
            raise e.__cause__.__cause__  # type: ignore


async def receive_models(model_type: type[SQLModelSubClass]) -> list[SQLModelSubClass]:
    """The function that returns all models of the given model type"""

    query = select(model_type)
    return (await execute_db_query(query)).scalars().fetchall()


async def receive_model(model_type: type[SQLModelSubClass], *conditions: BinaryExpression) -> SQLModelSubClass | None:
    """The function that returns the model by id from the database"""

    query = select(model_type).where(*conditions)
    return (await execute_db_query(query)).scalar()


async def update_models(model_type: type[SQLModelSubClass], data: SQLModel,
                        *conditions: BinaryExpression) -> int | None:
    """
    The function that updates models and returns the number of updated rows
    if the update is successful, otherwise None
    """

    query = update(model_type).values(data.dict(exclude_none=True)).where(*conditions)
    try:
        return (await execute_db_query(query)).rowcount  # type: ignore
    except IntegrityError:
        return None


async def delete_models(model_type: type[SQLModelSubClass], *conditions: BinaryExpression) -> int:
    """The function that deletes models from the database and returns the number of deleted rows"""

    query = delete(model_type).where(*conditions)
    row_count = (await execute_db_query(query)).rowcount  # type: ignore
    return row_count


def is_user_in_blacklist(user_id: int) -> bool:
    """The function that checks if the user is blacklisted"""

    return redis_engine.sismember(config.USERS_BLACKLIST_NAME, user_id)
