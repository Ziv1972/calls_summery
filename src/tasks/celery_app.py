"""Celery application configuration."""

from celery import Celery

from src.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "calls_summery",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "src.tasks.transcription_tasks",
        "src.tasks.summarization_tasks",
        "src.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry config
    task_default_retry_delay=60,
    task_max_retries=3,
)
