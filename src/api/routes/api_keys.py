"""API key management routes."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.api_key import ApiKey
from src.models.user import User
from src.schemas.auth import ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyResponse
from src.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=ApiResponse[ApiKeyCreatedResponse], status_code=201)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new API key. The full key is shown only once."""
    from src.services.auth_service import generate_api_key

    full_key, prefix, key_hash = generate_api_key()

    api_key = ApiKey(
        user_id=current_user.id,
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    logger.info("API key created: %s for user %s", prefix, current_user.email)

    return ApiResponse(
        success=True,
        data=ApiKeyCreatedResponse(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            full_key=full_key,
            created_at=api_key.created_at,
        ),
    )


@router.get("/", response_model=ApiResponse[list[ApiKeyResponse]])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all API keys for the current user."""
    result = await session.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return ApiResponse(
        success=True,
        data=[ApiKeyResponse.model_validate(k) for k in keys],
    )


@router.delete("/{key_id}", response_model=ApiResponse)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Revoke (deactivate) an API key."""
    result = await session.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    await session.commit()

    logger.info("API key revoked: %s for user %s", api_key.key_prefix, current_user.email)

    return ApiResponse(success=True, data={"message": "API key revoked"})
