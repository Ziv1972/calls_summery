"""Auth routes - register, login, refresh, me."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.user import User
from src.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.schemas.common import ApiResponse
from src.services.auth_service import (
    authenticate_user,
    create_token_pair,
    decode_token,
    hash_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    """Register a new user."""
    # Check if email already taken
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info("User registered: %s", user.email)
    return ApiResponse(success=True, data=UserResponse.model_validate(user))


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Login and receive JWT tokens."""
    user = await authenticate_user(session, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tokens = create_token_pair(user.id)
    logger.info("User logged in: %s", user.email)

    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        ),
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token using refresh token."""
    import uuid

    import jwt

    try:
        payload = decode_token(body.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user = await session.get(User, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    tokens = create_token_pair(user.id)

    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        ),
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return ApiResponse(success=True, data=UserResponse.model_validate(current_user))
