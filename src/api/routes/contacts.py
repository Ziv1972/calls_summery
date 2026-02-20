"""Contact API endpoints - CRUD, sync, and search."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.user import User
from src.repositories.call_repository import CallRepository
from src.repositories.contact_repository import ContactRepository
from src.schemas.call import CallResponse
from src.schemas.common import ApiResponse, PaginatedResponse
from src.schemas.contact import (
    ContactCreateRequest,
    ContactResponse,
    ContactSyncRequest,
    ContactUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    page: int = 1,
    page_size: int = 50,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List user contacts with optional search."""
    contact_repo = ContactRepository(session)

    if q:
        items = await contact_repo.search(current_user.id, q, limit=page_size)
        return PaginatedResponse(
            items=[ContactResponse.model_validate(c) for c in items],
            total=len(items),
            page=1,
            page_size=page_size,
            total_pages=1,
        )

    result = await contact_repo.find_by_user(current_user.id, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[ContactResponse.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{contact_id}", response_model=ApiResponse[ContactResponse])
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a contact by ID."""
    contact_repo = ContactRepository(session)
    contact = await contact_repo.find_by_id(contact_id)

    if contact is None or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    return ApiResponse(success=True, data=ContactResponse.model_validate(contact))


@router.post("/", response_model=ApiResponse[ContactResponse])
async def create_contact(
    body: ContactCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new contact."""
    contact_repo = ContactRepository(session)

    # Check for duplicate phone number
    existing = await contact_repo.find_by_phone(current_user.id, body.phone_number)
    if existing:
        raise HTTPException(status_code=409, detail="Contact with this phone number already exists")

    contact = await contact_repo.create({
        "user_id": current_user.id,
        "phone_number": body.phone_number,
        "name": body.name,
        "company": body.company,
        "email": body.email,
        "notes": body.notes,
    })
    await session.commit()

    return ApiResponse(success=True, data=ContactResponse.model_validate(contact))


@router.put("/{contact_id}", response_model=ApiResponse[ContactResponse])
async def update_contact(
    contact_id: uuid.UUID,
    body: ContactUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a contact."""
    contact_repo = ContactRepository(session)
    contact = await contact_repo.find_by_id(contact_id)

    if contact is None or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    updated = await contact_repo.update(contact_id, update_data)
    await session.commit()

    return ApiResponse(success=True, data=ContactResponse.model_validate(updated))


@router.delete("/{contact_id}", response_model=ApiResponse)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a contact."""
    contact_repo = ContactRepository(session)
    contact = await contact_repo.find_by_id(contact_id)

    if contact is None or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    await contact_repo.delete(contact_id)
    await session.commit()

    return ApiResponse(success=True, data={"message": "Contact deleted"})


@router.post("/sync", response_model=ApiResponse)
async def sync_contacts(
    body: ContactSyncRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Bulk sync contacts from mobile device. Upserts by phone number."""
    contact_repo = ContactRepository(session)
    contacts_data = [item.model_dump() for item in body.contacts]

    count = await contact_repo.bulk_upsert(current_user.id, contacts_data)
    await session.commit()

    logger.info("Synced %d contacts for user %s", count, current_user.id)
    return ApiResponse(success=True, data={"synced": count})


@router.get("/{contact_id}/calls", response_model=PaginatedResponse[CallResponse])
async def get_contact_calls(
    contact_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all calls linked to a specific contact."""
    contact_repo = ContactRepository(session)
    contact = await contact_repo.find_by_id(contact_id)

    if contact is None or contact.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    call_repo = CallRepository(session)
    result = await call_repo.find_by_contact(contact_id, page=page, page_size=page_size)

    return PaginatedResponse(
        items=[CallResponse.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )
