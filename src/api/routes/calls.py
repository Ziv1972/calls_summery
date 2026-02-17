"""Call API endpoints - upload, list, get, status, reprocess, delete."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import delete as sql_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.config.settings import get_settings
from src.models.call import CallStatus, UploadSource
from src.models.user import User
from src.repositories.call_repository import CallRepository
from src.schemas.call import CallResponse, CallStatusResponse, CallUploadRequest
from src.schemas.common import ApiResponse, PaginatedResponse
from src.services.call_service import CallService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/upload", response_model=ApiResponse[CallResponse])
async def upload_call(
    file: UploadFile,
    language: str = "auto",
    upload_source: str = "manual",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload a call recording and start processing."""
    settings = get_settings()

    # Validate content type
    if file.content_type not in settings.allowed_audio_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {file.content_type}. "
            f"Allowed: {settings.allowed_audio_formats}",
        )

    # Validate file size (hard ceiling)
    max_size = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB",
        )
    await file.seek(0)

    # Enforce plan limits
    from src.config.plan_limits import get_plan_limits

    limits = get_plan_limits(current_user.plan)
    plan_max_bytes = limits.max_file_size_mb * 1024 * 1024
    if len(content) > plan_max_bytes:
        raise HTTPException(
            status_code=403,
            detail=f"File exceeds {limits.max_file_size_mb}MB limit for your {current_user.plan.value} plan",
        )

    if limits.calls_per_month is not None:
        call_repo_check = CallRepository(session)
        count = await call_repo_check.count_calls_this_month(current_user.id)
        if count >= limits.calls_per_month:
            raise HTTPException(
                status_code=403,
                detail=f"Monthly limit of {limits.calls_per_month} calls reached for {current_user.plan.value} plan",
            )

    # Upload and create record
    call_service = CallService(session)
    source = UploadSource(upload_source) if upload_source in UploadSource.__members__.values() else UploadSource.MANUAL

    call_id = await call_service.upload_call(
        file_data=file.file,
        original_filename=file.filename or "unknown.mp3",
        content_type=file.content_type or "audio/mpeg",
        upload_source=source,
        user_id=current_user.id,
    )

    # Trigger async processing via Celery
    from src.tasks.transcription_tasks import process_transcription

    process_transcription.delay(str(call_id), language)

    # Fetch created call for response
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)

    return ApiResponse(
        success=True,
        data=CallResponse.model_validate(call),
    )


@router.get("/", response_model=PaginatedResponse[CallResponse])
async def list_calls(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all calls for the current user with pagination."""
    call_repo = CallRepository(session)
    result = await call_repo.find_by_user(current_user.id, page=page, page_size=page_size)

    return PaginatedResponse(
        items=[CallResponse.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{call_id}", response_model=ApiResponse[CallResponse])
async def get_call(
    call_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get call details by ID (must belong to current user)."""
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)

    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Call not found")

    return ApiResponse(success=True, data=CallResponse.model_validate(call))


@router.get("/{call_id}/status", response_model=ApiResponse[CallStatusResponse])
async def get_call_status(
    call_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get processing status for a call (must belong to current user)."""
    # Verify ownership
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)
    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Call not found")

    call_service = CallService(session)

    try:
        status = await call_service.get_processing_status(call_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Call not found")

    return ApiResponse(
        success=True,
        data=CallStatusResponse(
            call_id=status.call_id,
            status=status.call_status,
            transcription_status=status.transcription_status,
            summary_status=status.summary_status,
            error_message=status.error_message,
        ),
    )


async def _delete_call_children(session: AsyncSession, call_id: uuid.UUID) -> None:
    """Delete child records in FK order: notifications -> summaries -> transcriptions."""
    from src.models.notification import Notification
    from src.models.summary import Summary
    from src.models.transcription import Transcription

    # Notifications reference summaries, not calls directly
    await session.execute(
        sql_delete(Notification).where(
            Notification.summary_id.in_(
                select(Summary.id).where(Summary.call_id == call_id)
            )
        )
    )
    await session.execute(
        sql_delete(Summary).where(Summary.call_id == call_id)
    )
    await session.execute(
        sql_delete(Transcription).where(Transcription.call_id == call_id)
    )


@router.post("/{call_id}/reprocess", response_model=ApiResponse[CallResponse])
async def reprocess_call(
    call_id: uuid.UUID,
    language: str = "he",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Reset a failed call and re-trigger the processing pipeline."""
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)

    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Call not found")

    if call.status != CallStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Only failed calls can be reprocessed. Current status: {call.status.value}",
        )

    # Delete child records
    await _delete_call_children(session, call_id)

    # Reset call fields
    await call_repo.update(call_id, {
        "status": CallStatus.UPLOADED,
        "error_message": None,
        "language_detected": None,
    })
    await session.commit()

    # Re-trigger Celery pipeline
    from src.tasks.transcription_tasks import process_transcription

    process_transcription.delay(str(call_id), language)

    call = await call_repo.find_by_id(call_id)
    logger.info("Call %s reprocessed by user %s", call_id, current_user.id)
    return ApiResponse(success=True, data=CallResponse.model_validate(call))


@router.delete("/{call_id}", response_model=ApiResponse)
async def delete_call(
    call_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Permanently delete a call, its children, and the S3 file."""
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)

    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Call not found")

    s3_key = call.s3_key

    # Delete child records in FK order
    await _delete_call_children(session, call_id)

    # Delete the call itself
    await session.delete(call)
    await session.commit()

    # Best-effort S3 deletion
    try:
        from src.services.storage_service import StorageService

        storage = StorageService()
        storage.delete_file(s3_key)
    except Exception:
        logger.warning("S3 delete failed for key %s (call already deleted from DB)", s3_key)

    logger.info("Call %s deleted by user %s", call_id, current_user.id)
    return ApiResponse(success=True, data={"message": "Call deleted"})
