from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from settings import settings


DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)
Base = declarative_base()


def table_exists(engine, table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


async def get_db():
    async with async_session() as session:
    # db = async_session()
        try:
            yield session
        finally:
            await session.close()
