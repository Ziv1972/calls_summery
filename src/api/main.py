"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.api.routes import api_keys, auth, calls, health, notifications, settings as settings_routes, summaries, webhooks
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

    @app.get("/")
    async def root():
        return RedirectResponse(url="/docs")

    # Register routes
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(calls.router, prefix="/api")
    app.include_router(summaries.router, prefix="/api")
    app.include_router(webhooks.router, prefix="/api")
    app.include_router(settings_routes.router, prefix="/api")
    app.include_router(api_keys.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")

    return app


app = create_app()
