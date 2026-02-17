"""Notification repository - data access for notification records."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import Notification
from src.repositories.base import BaseRepository, PaginationResult


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    async def find_by_user(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginationResult[Notification]:
        """Find notifications for a user's calls (via summary -> call -> user)."""
        from src.models.call import Call
        from src.models.summary import Summary

        # Count total
        count_query = (
            select(Notification)
            .join(Summary, Notification.summary_id == Summary.id)
            .join(Call, Summary.call_id == Call.id)
            .where(Call.user_id == user_id)
        )
        count_result = await self._session.execute(count_query)
        total = len(count_result.scalars().all())

        # Fetch page
        offset = (page - 1) * page_size
        query = (
            select(Notification)
            .join(Summary, Notification.summary_id == Summary.id)
            .join(Call, Summary.call_id == Call.id)
            .where(Call.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        items = result.scalars().all()

        return PaginationResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
