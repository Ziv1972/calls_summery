#!/bin/sh
set -e

# If a command is passed (from docker-compose `command:`), run it directly
if [ $# -gt 0 ]; then
    # Run migrations only for the API service
    if echo "$@" | grep -q "gunicorn\|uvicorn"; then
        echo "Running database migrations..."
        alembic upgrade head
    fi
    echo "Starting: $@"
    exec "$@"
fi

# Default: entrypoint decides based on SERVICE_TYPE
if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A src.tasks.celery_app worker --loglevel=info --pool=solo
else
    echo "Running database migrations..."
    alembic upgrade head
    echo "Starting API server..."
    exec gunicorn src.api.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120
fi
