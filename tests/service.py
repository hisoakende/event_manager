import unittest
from unittest.mock import Mock

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src import database
from tests.config import TEST_DATABASE_URL


class DBProcessedIsolatedAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    tables = ('user', 'refreshtoken')

    async def asyncSetUp(self) -> None:
        database.engine = create_async_engine(TEST_DATABASE_URL)
        database.Session = sessionmaker(database.engine, class_=AsyncSession, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        async with database.engine.begin() as conn:
            for table in self.tables:
                await conn.execute(text(f'DELETE FROM public.{table}'))
        await database.engine.dispose()
