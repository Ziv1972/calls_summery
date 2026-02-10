"""Settings endpoints for user preferences."""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.models.settings import NotificationMethod, UserSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Settings response schema."""

    summary_language: str = "auto"
    email_recipient: str | None = None
    whatsapp_recipient: str | None = None
    notify_on_complete: bool = True
    notification_method: str = "email"
    auto_upload_enabled: bool = True


class SettingsUpdate(BaseModel):
    """Settings update schema."""

    summary_language: str | None = None
    email_recipient: str | None = None
    whatsapp_recipient: str | None = None
    notify_on_complete: bool | None = None
    notification_method: str | None = None
    auto_upload_enabled: bool | None = None


async def _get_or_create_settings(session: AsyncSession) -> UserSettings:
    """Get the single settings row, or create default if missing."""
    result = await session.execute(select(UserSettings).limit(1))
    settings = result.scalar_one_or_none()

    if settings is None:
        settings = UserSettings()
        session.add(settings)
        await session.flush()
        await session.refresh(settings)

    return settings


@router.get("")
async def get_settings(session: AsyncSession = Depends(get_session)):
    """Get current user settings."""
    settings = await _get_or_create_settings(session)

    return {
        "success": True,
        "data": SettingsResponse(
            summary_language=settings.summary_language,
            email_recipient=settings.email_recipient,
            whatsapp_recipient=settings.whatsapp_recipient,
            notify_on_complete=settings.notify_on_complete,
            notification_method=settings.notification_method.value,
            auto_upload_enabled=settings.auto_upload_enabled,
        ).model_dump(),
    }


@router.put("")
async def update_settings(
    update: SettingsUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update user settings."""
    settings = await _get_or_create_settings(session)

    if update.summary_language is not None:
        settings.summary_language = update.summary_language

    if update.email_recipient is not None:
        settings.email_recipient = update.email_recipient

    if update.whatsapp_recipient is not None:
        settings.whatsapp_recipient = update.whatsapp_recipient

    if update.notify_on_complete is not None:
        settings.notify_on_complete = update.notify_on_complete

    if update.notification_method is not None:
        settings.notification_method = NotificationMethod(update.notification_method)

    if update.auto_upload_enabled is not None:
        settings.auto_upload_enabled = update.auto_upload_enabled

    await session.commit()
    await session.refresh(settings)

    logger.info("Settings updated: notify=%s, method=%s", settings.notify_on_complete, settings.notification_method)

    return {
        "success": True,
        "data": SettingsResponse(
            summary_language=settings.summary_language,
            email_recipient=settings.email_recipient,
            whatsapp_recipient=settings.whatsapp_recipient,
            notify_on_complete=settings.notify_on_complete,
            notification_method=settings.notification_method.value,
            auto_upload_enabled=settings.auto_upload_enabled,
        ).model_dump(),
    }
