"""Common schemas shared across the application."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool
    data: T | None = None
    error: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatusResponse(BaseModel):
    """Simple status response."""

    status: str
    message: str | None = None
