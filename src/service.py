from typing import Any

from sqlalchemy.engine import Result

from src import database


async def execute_db_query(query: Any) -> Result:
    """The function that executes the given query to db"""

    async with database.Session() as session, session.begin():
        return await session.execute(query)
