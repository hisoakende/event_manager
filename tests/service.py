import unittest

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src import database
from tests.config import TEST_DATABASE_URL


class DBProcessedIsolatedAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    tables = ('user', 'refreshtoken', 'event', 'govstructure')
    test_endpoint = False

    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine(TEST_DATABASE_URL)
        self.Session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        if not self.test_endpoint:
            database.engine = create_async_engine(TEST_DATABASE_URL)
            database.Session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            for table in self.tables:
                await conn.execute(text(f'DELETE FROM public.{table}'))

        await self.engine.dispose()

        if not self.test_endpoint:
            await database.engine.dispose()
