"""Database engine and session setup for async PostgreSQL."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def create_engine():
    """Create async database engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
    )


def create_session_factory(engine=None):
    """Create async session factory."""
    if engine is None:
        engine = create_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    """Yield an async database session."""
    engine = create_engine()
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
