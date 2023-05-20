import json
import uuid as uuid_pkg
from typing import Any, TypeVar

import aiosmtplib
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import SQLModel

import src
from src import database, config
from src.redis_ import redis_engine
from src.sfp import SortingFilteringPaging
from src.utils import EmailMessage

SQLModelSubClass = TypeVar('SQLModelSubClass', bound=SQLModel)


async def execute_db_query(query: Any) -> Result:
    """The function that executes the given query to db"""

    async with database.Session() as session, session.begin():
        return await session.execute(query)


async def create_model(model: SQLModelSubClass) -> None:
    """The function that creates model"""

    async with database.Session() as session:
        session.add(model)

        try:
            await session.commit()
        except IntegrityError as e:
            raise e.__cause__.__cause__  # type: ignore


async def receive_models_by_sfp_or_filter(model_type: type[SQLModelSubClass],
                                          model_sfp_or_filter: Filter) -> list[SQLModelSubClass]:
    """The function that returns models using sorting, filtering and, if necessary, pagination"""

    query = model_sfp_or_filter.sort(model_sfp_or_filter.filter(select(model_type)))
    if isinstance(model_sfp_or_filter, SortingFilteringPaging):
        query = model_sfp_or_filter.paginate(query)

    return (await execute_db_query(query)).scalars().fetchall()


async def receive_model(model_type: type[SQLModelSubClass], *conditions: BinaryExpression) -> SQLModelSubClass | None:
    """The function that returns the model by id from the database"""

    query = select(model_type).where(*conditions)
    return (await execute_db_query(query)).scalar()


async def update_models(model_type: type[SQLModelSubClass], data: BaseModel,
                        *conditions: BinaryExpression) -> int | None:
    """
    The function that updates models and returns the number of updated rows
    if the update is successful, otherwise raise the base exception
    """

    query = update(model_type).values(data.dict(exclude_unset=True)).where(*conditions)

    try:
        row_count = (await execute_db_query(query)).rowcount  # type: ignore
    except IntegrityError as e:
        raise e.__cause__.__cause__  # type: ignore

    return row_count


async def delete_models(model_type: type[SQLModelSubClass], *conditions: BinaryExpression) -> int:
    """The function that deletes models from the database and returns the number of deleted rows"""

    query = delete(model_type).where(*conditions)
    row_count = (await execute_db_query(query)).rowcount  # type: ignore
    return row_count


def is_user_in_blacklist(user_id: int) -> bool:
    """The function that checks if the user is blacklisted in redis"""

    return redis_engine.sismember(config.USERS_BLACKLIST_NAME, user_id)


async def send_email(message: EmailMessage) -> None:
    """The function that sends email"""

    async with aiosmtplib.SMTP(hostname=src.config.EMAIL_HOST, port=src.config.EMAIL_PORT) as server:
        await server.login(src.config.EMAIL_LOCAL_ADDRESS, src.config.EMAIL_PASSWORD)
        await server.send_message(message.create())


def set_unconfirmed_email_data(confirmation_uuid: uuid_pkg.UUID, data: SQLModelSubClass) -> None:
    """The function that saves data with unconfirmed email in redis"""

    redis_engine.set(f'{confirmation_uuid}-{data.__class__.__name__}', data.json(), ex=1800)


def receive_unconfirmed_email_data(confirmation_uuid: uuid_pkg.UUID,
                                   data_class: type[SQLModelSubClass]) -> SQLModelSubClass | None:
    """The function that returns data with unconfirmed email from redis"""

    redis_data = redis_engine.get(f'{confirmation_uuid}-{data_class.__name__}')
    if redis_data is None:
        return None

    return data_class(**json.loads(redis_data))


def delete_unconfirmed_email_data(confirmation_uuid: uuid_pkg.UUID,
                                  data_class: type[SQLModelSubClass]) -> None:
    """The function that deletes data with unconfirmed email from redis"""

    redis_engine.delete(f'{confirmation_uuid}-{data_class.__name__}')
