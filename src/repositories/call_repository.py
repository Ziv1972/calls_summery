"""Call repository - data access for call records."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.call import Call, CallStatus
from src.repositories.base import BaseRepository, PaginationResult


class CallRepository(BaseRepository[Call]):
    """Repository for Call entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Call)

    async def find_by_status(self, status: CallStatus) -> list[Call]:
        """Find all calls with a given status."""
        query = select(Call).where(Call.status == status).order_by(Call.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def find_by_user(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        contact_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sentiment: str | None = None,
        status: str | None = None,
    ) -> PaginationResult[Call]:
        """Find calls for a user with pagination and optional filters."""
        base_filter = [Call.user_id == user_id]

        if contact_id is not None:
            base_filter.append(Call.contact_id == contact_id)
        if date_from is not None:
            base_filter.append(Call.created_at >= date_from)
        if date_to is not None:
            base_filter.append(Call.created_at <= date_to)
        if status is not None:
            base_filter.append(Call.status == status)

        # Sentiment filter requires joining summaries
        if sentiment is not None:
            from src.models.summary import Summary

            count_query = (
                select(func.count())
                .select_from(Call)
                .join(Summary, Summary.call_id == Call.id)
                .where(*base_filter, Summary.sentiment == sentiment)
            )
        else:
            count_query = select(func.count()).select_from(Call).where(*base_filter)

        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size

        if sentiment is not None:
            from src.models.summary import Summary

            query = (
                select(Call)
                .join(Summary, Summary.call_id == Call.id)
                .where(*base_filter, Summary.sentiment == sentiment)
                .order_by(Call.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        else:
            query = (
                select(Call)
                .where(*base_filter)
                .order_by(Call.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )

        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return PaginationResult(items=items, total=total, page=page, page_size=page_size)

    async def find_by_contact(
        self, contact_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> PaginationResult[Call]:
        """Find all calls linked to a contact."""
        count_query = select(func.count()).select_from(Call).where(Call.contact_id == contact_id)
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Call)
            .where(Call.contact_id == contact_id)
            .order_by(Call.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return PaginationResult(items=items, total=total, page=page, page_size=page_size)

    @staticmethod
    def _escape_like(text: str) -> str:
        """Escape special LIKE/ILIKE characters in user input."""
        return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    async def search(
        self, user_id: uuid.UUID, query_text: str, page: int = 1, page_size: int = 20
    ) -> PaginationResult[Call]:
        """Search across summaries, transcriptions, and filenames for a user's calls."""
        from src.models.summary import Summary
        from src.models.transcription import Transcription

        escaped = self._escape_like(query_text)
        pattern = f"%{escaped}%"

        base_query = (
            select(Call)
            .outerjoin(Summary, Summary.call_id == Call.id)
            .outerjoin(Transcription, Transcription.call_id == Call.id)
            .where(
                Call.user_id == user_id,
                or_(
                    Summary.summary_text.ilike(pattern),
                    Transcription.text.ilike(pattern),
                    Call.original_filename.ilike(pattern),
                ),
            )
            .distinct()
        )

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        query = base_query.order_by(Call.created_at.desc()).offset(offset).limit(page_size)
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return PaginationResult(items=items, total=total, page=page, page_size=page_size)

    async def find_by_s3_key(self, s3_key: str) -> Call | None:
        """Find a call by its S3 key."""
        query = select(Call).where(Call.s3_key == s3_key)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def count_calls_this_month(self, user_id: uuid.UUID) -> int:
        """Count calls created by user in the current calendar month."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = (
            select(func.count())
            .select_from(Call)
            .where(
                Call.user_id == user_id,
                Call.created_at >= month_start,
            )
        )
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def update_status(
        self, call_id: uuid.UUID, status: CallStatus, error_message: str | None = None
    ) -> Call | None:
        """Update call status with optional error message."""
        data: dict = {"status": status}
        if error_message is not None:
            data["error_message"] = error_message
        return await self.update(call_id, data)
