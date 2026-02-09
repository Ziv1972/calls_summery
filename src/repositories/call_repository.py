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
