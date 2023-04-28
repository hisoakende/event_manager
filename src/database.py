from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config import DATABASE_URL

engine: AsyncEngine = None  # type: ignore
Session: sessionmaker = None  # type: ignore


def db_startup() -> None:
    global engine, Session
    engine = create_async_engine(DATABASE_URL, echo=True)
    Session = sessionmaker(engine, class_=AsyncSession)


async def db_shutdown() -> None:
    await engine.dispose()
