"""Summary API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.user import User
from src.repositories.call_repository import CallRepository
from src.repositories.summary_repository import SummaryRepository
from src.repositories.transcription_repository import TranscriptionRepository
from src.schemas.common import ApiResponse
from src.schemas.summary import CallDetailResponse, CallResponseMinimal, SummaryResponse, TranscriptionResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/call/{call_id}", response_model=ApiResponse[CallDetailResponse])
async def get_call_detail(
    call_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get full call detail with transcription and summary."""
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(call_id)
    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Call not found")

    transcription_repo = TranscriptionRepository(session)
    transcription = await transcription_repo.find_by_call_id(call_id)

    summary_repo = SummaryRepository(session)
    summary = await summary_repo.find_latest_by_call_id(call_id)

    return ApiResponse(
        success=True,
        data=CallDetailResponse(
            call=CallResponseMinimal.model_validate(call),
            transcription=TranscriptionResponse.model_validate(transcription) if transcription else None,
            summary=SummaryResponse.model_validate(summary) if summary else None,
        ),
    )


@router.get("/{summary_id}", response_model=ApiResponse[SummaryResponse])
async def get_summary(
    summary_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get summary by ID (must belong to current user's call)."""
    summary_repo = SummaryRepository(session)
    summary = await summary_repo.find_by_id(summary_id)

    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")

    # Verify the summary's call belongs to current user
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(summary.call_id)
    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Summary not found")

    return ApiResponse(
        success=True,
        data=SummaryResponse.model_validate(summary),
    )
