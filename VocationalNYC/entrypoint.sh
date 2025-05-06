#!/bin/sh
set -e

# If any arguments are passed, run them (used for migrations, etc.)
if [ "$#" -gt 0 ]; then
    echo "Running command: $@"
    exec "$@"
fi

# Otherwise, start the server depending on environment
if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting in development mode with runserver..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Starting in production mode with Gunicorn..."
    exec gunicorn vocationalnyc.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
fi