"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import calls, health, summaries, webhooks
from src.config.logging import setup_logging
from src.config.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    app = FastAPI(
        title=settings.app_name,
        description="Phone call transcription and summarization service",
        version="0.1.0",
        debug=settings.debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router, prefix="/api")
    app.include_router(calls.router, prefix="/api")
    app.include_router(summaries.router, prefix="/api")
    app.include_router(webhooks.router, prefix="/api")

    return app


app = create_app()
