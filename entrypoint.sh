#!/bin/sh
set -e

if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A src.tasks.celery_app worker --loglevel=info --pool=solo
else
    echo "Running database migrations..."
    alembic upgrade head
    echo "Starting API server..."
    exec gunicorn src.api.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120
fi
