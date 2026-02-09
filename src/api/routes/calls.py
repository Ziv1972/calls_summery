"""Call API endpoints - upload, list, get, status."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.config.settings import get_settings
from src.models.call import UploadSource
from src.repositories.call_repository import CallRepository
from src.schemas.call import CallResponse, CallStatusResponse, CallUploadRequest
from src.schemas.common import ApiResponse, PaginatedResponse
from src.services.call_service import CallService

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/upload", response_model=ApiResponse[CallResponse])
async def upload_call(
    file: UploadFile,
    language: str = "auto",
    upload_source: str = "manual",
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

    # Validate file size
    max_size = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB",
        )
    await file.seek(0)

    # Upload and create record
    call_service = CallService(session)
    source = UploadSource(upload_source) if upload_source in UploadSource.__members__.values() else UploadSource.MANUAL

    call_id = await call_service.upload_call(
        file_data=file.file,
        original_filename=file.filename or "unknown.mp3",
        content_type=file.content_type or "audio/mpeg",
        upload_source=source,
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
    session: AsyncSession = Depends(get_session),
):
    """List all calls with pagination."""
    call_repo = CallRepository(session)
    result = await call_repo.find_all(page=page, page_size=page_size)

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
    session: AsyncSession = Depends(get_session),
):
    """Get call details by ID."""
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)

    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    return ApiResponse(success=True, data=CallResponse.model_validate(call))


@router.get("/{call_id}/status", response_model=ApiResponse[CallStatusResponse])
async def get_call_status(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get processing status for a call."""
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
