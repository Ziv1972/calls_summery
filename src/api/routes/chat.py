"""Chat route - AI companion endpoint for the desktop/web app."""

from __future__ import annotations

import logging
from typing import Any

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)
    system_prompt: str = Field("", max_length=5000)


class ChatResponse(BaseModel):
    response: str


@router.post("/", response_model=dict[str, Any])
async def chat(
    request: ChatRequest,
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Send messages to Claude and get a response."""
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="AI chat not configured")

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            system=request.system_prompt or "You are a helpful assistant.",
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
        )

        text = response.content[0].text if response.content[0].type == "text" else ""
        return {"success": True, "data": {"response": text}, "error": None}

    except anthropic.APIError as exc:
        logger.error("Anthropic API error in chat: %s", exc)
        raise HTTPException(status_code=502, detail="AI service error") from exc
    except Exception as exc:
        logger.exception("Unexpected chat error")
        raise HTTPException(status_code=500, detail="Internal error") from exc
