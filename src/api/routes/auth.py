"""Auth routes - register, login, refresh, me, email verification, plan management."""

import logging
import uuid

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
    UpgradePlanRequest,
    UserResponse,
    VerifyEmailRequest,
)
from src.schemas.common import ApiResponse, StatusResponse
from src.services.auth_service import (
    authenticate_user,
    create_email_verification_token,
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

    # Send verification email (best-effort)
    try:
        from src.services.email_service import EmailService

        verify_token = create_email_verification_token(user.id)
        email_svc = EmailService()
        email_svc.send_verification_email(user.email, verify_token)
    except Exception:
        logger.warning("Could not send verification email to %s", user.email)

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


@router.post("/verify-email", response_model=ApiResponse[UserResponse])
async def verify_email(
    body: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify user email address using a verification token."""
    import jwt

    try:
        payload = decode_token(body.token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification link has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if payload.type != "email_verify":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user = await session.get(User, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return ApiResponse(success=True, data=UserResponse.model_validate(user))

    user.is_verified = True
    await session.commit()
    await session.refresh(user)

    logger.info("User email verified: %s", user.email)
    return ApiResponse(success=True, data=UserResponse.model_validate(user))


@router.post("/resend-verification", response_model=ApiResponse[StatusResponse])
async def resend_verification(
    current_user: User = Depends(get_current_user),
):
    """Resend email verification link."""
    if current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    from src.services.email_service import EmailService

    token = create_email_verification_token(current_user.id)
    email_svc = EmailService()
    result = email_svc.send_verification_email(current_user.email, token)

    if not result.success:
        logger.error("Resend verification failed for %s: %s", current_user.email, result.error)
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return ApiResponse(success=True, data=StatusResponse(status="sent"))


@router.post("/upgrade-plan", response_model=ApiResponse[UserResponse])
async def upgrade_plan(
    body: UpgradePlanRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change the current user's plan (no payment, admin-style for now)."""
    current_user.plan = body.plan
    await session.commit()
    await session.refresh(current_user)
    logger.info("User %s plan changed to %s", current_user.email, body.plan.value)
    return ApiResponse(success=True, data=UserResponse.model_validate(current_user))


@router.get("/usage", response_model=ApiResponse[dict])
async def get_usage(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's plan usage summary."""
    from src.config.plan_limits import get_plan_limits
    from src.repositories.call_repository import CallRepository

    limits = get_plan_limits(current_user.plan)
    repo = CallRepository(session)
    calls_this_month = await repo.count_calls_this_month(current_user.id)

    return ApiResponse(
        success=True,
        data={
            "plan": current_user.plan.value,
            "calls_this_month": calls_this_month,
            "calls_limit": limits.calls_per_month,
            "max_file_size_mb": limits.max_file_size_mb,
        },
    )
