from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src import config

engine: AsyncEngine = None  # type: ignore
Session: sessionmaker = None  # type: ignore


def db_startup() -> None:
    """The function that processes the start of the database interaction"""

    global engine, Session
    engine = create_async_engine(config.DATABASE_URL, echo=True)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def db_shutdown() -> None:
    """The function that processes the stop of the database interaction"""

    await engine.dispose()
