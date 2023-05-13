import asyncio
import logging
import os
import unittest

import alembic.config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

import src.auth.models
import src.config
import src.events.models
import src.gov_structures.models
import src.users.models
from tests import config
from tests.config import TEST_USERS_BLACKLIST_NAME, TEST_DATABASE_URL

alembicArgs = ['upgrade', 'head']


def set_up() -> None:
    src.config.USERS_BLACKLIST_NAME = TEST_USERS_BLACKLIST_NAME
    src.config.DATABASE_URL = TEST_DATABASE_URL

    alembic.config.main(argv=alembicArgs)


async def tear_down() -> None:
    engine = create_async_engine(config.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.execute(text('DROP TABLE alembic_version'))

    await engine.dispose()


def main() -> None:
    set_up()

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.discover('tests'))

    logging.disable(logging.CRITICAL)
    runner = unittest.TextTestRunner()
    runner.run(suite)

    asyncio.run(tear_down())


if __name__ == '__main__':
    main()
