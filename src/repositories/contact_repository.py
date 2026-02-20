"""Contact repository - data access for contact records."""

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.models.contact import Contact
from src.repositories.base import BaseRepository, PaginationResult


class ContactRepository(BaseRepository[Contact]):
    """Repository for Contact entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Contact)

    async def find_by_user(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> PaginationResult[Contact]:
        """Find all contacts for a user with pagination."""
        count_query = select(func.count()).select_from(Contact).where(Contact.user_id == user_id)
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Contact)
            .where(Contact.user_id == user_id)
            .order_by(Contact.name.asc().nulls_last(), Contact.phone_number.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        items = result.scalars().all()

        return PaginationResult(items=items, total=total, page=page, page_size=page_size)

    async def find_by_phone(self, user_id: uuid.UUID, phone_number: str) -> Contact | None:
        """Find a contact by phone number for a specific user."""
        query = select(Contact).where(
            Contact.user_id == user_id,
            Contact.phone_number == phone_number,
        )
        result = await self._session.execute(query)
        return result.scalars().first()

    async def find_by_phones(self, user_id: uuid.UUID, phone_numbers: list[str]) -> Sequence[Contact]:
        """Find contacts matching any of the given phone numbers."""
        if not phone_numbers:
            return []
        query = select(Contact).where(
            Contact.user_id == user_id,
            Contact.phone_number.in_(phone_numbers),
        )
        result = await self._session.execute(query)
        return result.scalars().all()

    @staticmethod
    def _escape_like(text: str) -> str:
        """Escape special LIKE/ILIKE characters in user input."""
        return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    async def search(self, user_id: uuid.UUID, query_text: str, limit: int = 20) -> Sequence[Contact]:
        """Search contacts by name, phone, or company."""
        escaped = self._escape_like(query_text)
        pattern = f"%{escaped}%"
        query = (
            select(Contact)
            .where(
                Contact.user_id == user_id,
                (Contact.name.ilike(pattern))
                | (Contact.phone_number.ilike(pattern))
                | (Contact.company.ilike(pattern)),
            )
            .order_by(Contact.name.asc().nulls_last())
            .limit(limit)
        )
        result = await self._session.execute(query)
        return result.scalars().all()

    async def bulk_upsert(self, user_id: uuid.UUID, contacts: list[dict]) -> int:
        """Bulk insert or update contacts. Returns count of upserted records."""
        if not contacts:
            return 0

        rows = [
            {
                "user_id": user_id,
                "phone_number": c["phone_number"],
                "name": c.get("name"),
                "email": c.get("email"),
                "company": c.get("company"),
                "notes": c.get("notes"),
            }
            for c in contacts
        ]

        stmt = pg_insert(Contact).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_contact_user_phone",
            set_={
                "name": stmt.excluded.name,
                "email": stmt.excluded.email,
                "company": stmt.excluded.company,
                "notes": stmt.excluded.notes,
            },
        )

        await self._session.execute(stmt)
        await self._session.flush()
        return len(rows)
