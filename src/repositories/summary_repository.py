"""Summary repository - data access for summary records."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.summary import Summary, SummaryStatus
from src.repositories.base import BaseRepository


class SummaryRepository(BaseRepository[Summary]):
    """Repository for Summary entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Summary)

    async def find_by_call_id(self, call_id: uuid.UUID) -> Sequence[Summary]:
        """Find all summaries for a call."""
        query = (
            select(Summary)
            .where(Summary.call_id == call_id)
            .order_by(Summary.created_at.desc())
        )
        result = await self._session.execute(query)
        return result.scalars().all()

    async def find_latest_by_call_id(self, call_id: uuid.UUID) -> Summary | None:
        """Find the most recent summary for a call."""
        query = (
            select(Summary)
            .where(Summary.call_id == call_id)
            .order_by(Summary.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalars().first()

    async def update_status(
        self,
        summary_id: uuid.UUID,
        status: SummaryStatus,
        error_message: str | None = None,
    ) -> Summary | None:
        """Update summary status."""
        data: dict = {"status": status}
        if error_message is not None:
            data["error_message"] = error_message
        return await self.update(summary_id, data)
