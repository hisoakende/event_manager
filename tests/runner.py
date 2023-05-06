import asyncio
import unittest

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

import src.auth.models
import src.config
import src.users.models
from tests import config
from tests.config import TEST_USERS_BLACKLIST_NAME, TEST_DATABASE_URL


async def set_up() -> None:
    src.config.USERS_BLACKLIST_NAME = TEST_USERS_BLACKLIST_NAME
    src.config.DATABASE_URL = TEST_DATABASE_URL

    engine = create_async_engine(config.TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await engine.dispose()


async def tear_down() -> None:
    engine = create_async_engine(config.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


def main() -> None:
    asyncio.run(set_up())

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.discover('tests'))

    runner = unittest.TextTestRunner()
    runner.run(suite)

    asyncio.run(tear_down())


if __name__ == '__main__':
    main()
