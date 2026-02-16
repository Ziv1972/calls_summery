"""Call repository - data access for call records."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.call import Call, CallStatus
from src.repositories.base import BaseRepository


class CallRepository(BaseRepository[Call]):
    """Repository for Call entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Call)

    async def find_by_status(self, status: CallStatus) -> Sequence[Call]:
        """Find all calls with a given status."""
        query = select(Call).where(Call.status == status).order_by(Call.created_at.desc())
        result = await self._session.execute(query)
        return result.scalars().all()

    async def find_by_user(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ):
        """Find all calls for a user with pagination."""
        from sqlalchemy import func

        count_query = select(func.count()).select_from(Call).where(Call.user_id == user_id)
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Call)
            .where(Call.user_id == user_id)
            .order_by(Call.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        items = result.scalars().all()

        from src.repositories.base import PaginationResult

        return PaginationResult(items=items, total=total, page=page, page_size=page_size)

    async def find_by_s3_key(self, s3_key: str) -> Call | None:
        """Find a call by its S3 key."""
        query = select(Call).where(Call.s3_key == s3_key)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def update_status(
        self, call_id: uuid.UUID, status: CallStatus, error_message: str | None = None
    ) -> Call | None:
        """Update call status with optional error message."""
        data: dict = {"status": status}
        if error_message is not None:
            data["error_message"] = error_message
        return await self.update(call_id, data)
