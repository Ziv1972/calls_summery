"""Transcription repository - data access for transcription records."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transcription import Transcription, TranscriptionStatus
from src.repositories.base import BaseRepository


class TranscriptionRepository(BaseRepository[Transcription]):
    """Repository for Transcription entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Transcription)

    async def find_by_call_id(self, call_id: uuid.UUID) -> Transcription | None:
        """Find transcription by call ID."""
        query = select(Transcription).where(Transcription.call_id == call_id)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def find_by_external_id(self, external_id: str) -> Transcription | None:
        """Find transcription by provider's external ID."""
        query = select(Transcription).where(Transcription.external_id == external_id)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def update_status(
        self,
        transcription_id: uuid.UUID,
        status: TranscriptionStatus,
        error_message: str | None = None,
    ) -> Transcription | None:
        """Update transcription status."""
        data: dict = {"status": status}
        if error_message is not None:
            data["error_message"] = error_message
        return await self.update(transcription_id, data)
