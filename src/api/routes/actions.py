"""Action API endpoints - get action suggestions with deep links."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.user import User
from src.repositories.call_repository import CallRepository
from src.repositories.summary_repository import SummaryRepository
from src.schemas.common import ApiResponse
from src.services.action_service import generate_action_links

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/summary/{summary_id}", response_model=ApiResponse)
async def get_summary_actions(
    summary_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get structured actions with deep links for a summary."""
    summary_repo = SummaryRepository(session)
    summary = await summary_repo.find_by_id(summary_id)

    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")

    # Verify ownership through call
    call_repo = CallRepository(session)
    call = await call_repo.find_by_id(summary.call_id)
    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Summary not found")

    structured_actions = summary.structured_actions or []
    action_links = generate_action_links(structured_actions)

    return ApiResponse(
        success=True,
        data={
            "summary_id": str(summary_id),
            "actions": [
                {
                    "type": al.type,
                    "description": al.description,
                    "details": al.details,
                    "confidence": al.confidence,
                    "deep_link": al.deep_link,
                    "link_type": al.link_type,
                }
                for al in action_links
            ],
        },
    )
