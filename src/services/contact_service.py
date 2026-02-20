"""Contact service - business logic for contact matching and linking."""

import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.contact_repository import ContactRepository

logger = logging.getLogger(__name__)

# Pattern to match phone numbers (international and local Israeli formats)
_PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-()]{7,18}\d")


def extract_phone_numbers(participants_details: list[dict]) -> list[str]:
    """Extract phone numbers from participant details."""
    phones = []
    for p in participants_details:
        phone = p.get("phone")
        if phone and isinstance(phone, str):
            cleaned = normalize_phone(phone)
            if cleaned:
                phones.append(cleaned)
    return phones


def normalize_phone(phone: str) -> str | None:
    """Normalize phone number to digits-only format."""
    digits = re.sub(r"[^\d+]", "", phone)
    if len(digits) < 7:
        return None
    return digits


async def link_call_to_contact(
    session: AsyncSession,
    call_id: uuid.UUID,
    user_id: uuid.UUID,
    participants_details: list[dict],
) -> uuid.UUID | None:
    """Try to link a call to an existing contact based on extracted phone numbers.

    Returns contact_id if matched, None otherwise.
    """
    phones = extract_phone_numbers(participants_details)
    if not phones:
        return None

    contact_repo = ContactRepository(session)
    matched_contacts = await contact_repo.find_by_phones(user_id, phones)

    if not matched_contacts:
        return None

    # Use the first matched contact (typically the non-user participant)
    contact = matched_contacts[0]
    logger.info("Linked call %s to contact %s (%s)", call_id, contact.id, contact.name)
    return contact.id
