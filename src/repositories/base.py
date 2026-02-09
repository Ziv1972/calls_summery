"""Base repository with generic CRUD operations (immutable pattern)."""

import uuid
from dataclasses import dataclass
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import Base

ModelType = TypeVar("ModelType", bound=Base)


@dataclass(frozen=True)
class PaginationResult(Generic[ModelType]):
    """Immutable pagination result."""

    items: Sequence[ModelType]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


class BaseRepository(Generic[ModelType]):
    """Base repository implementing generic CRUD with immutable returns."""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self._session = session
        self._model = model

    async def find_by_id(self, entity_id: uuid.UUID) -> ModelType | None:
        """Find entity by ID."""
        return await self._session.get(self._model, entity_id)

    async def find_all(
        self,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> PaginationResult[ModelType]:
        """Find all entities with pagination."""
        # Count total
        count_query = select(self._model)
        count_result = await self._session.execute(count_query)
        total = len(count_result.scalars().all())

        # Fetch page
        column = getattr(self._model, order_by)
        order = column.desc() if descending else column.asc()
        offset = (page - 1) * page_size

        query = select(self._model).order_by(order).offset(offset).limit(page_size)
        result = await self._session.execute(query)
        items = result.scalars().all()

        return PaginationResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new entity from dict data."""
        entity = self._model(**data)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(
        self, entity_id: uuid.UUID, data: dict[str, Any]
    ) -> ModelType | None:
        """Update entity by ID. Returns updated entity or None."""
        entity = await self.find_by_id(entity_id)
        if entity is None:
            return None

        for key, value in data.items():
            setattr(entity, key, value)

        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        entity = await self.find_by_id(entity_id)
        if entity is None:
            return False

        await self._session.delete(entity)
        await self._session.flush()
        return True
