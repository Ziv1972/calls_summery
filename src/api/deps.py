"""FastAPI dependencies for dependency injection."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import create_engine, create_session_factory
from src.services.call_service import CallService

# Module-level engine and session factory (initialized once)
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_engine())
    return _session_factory


async def get_session():
    """Yield an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_call_service(session: AsyncSession) -> CallService:
    """Create CallService with injected session."""
    return CallService(session)
