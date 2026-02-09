"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Application health check."""
    return {"status": "healthy", "service": "calls-summery"}
