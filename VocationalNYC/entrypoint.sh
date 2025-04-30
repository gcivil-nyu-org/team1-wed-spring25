#!/bin/sh
set -e

# Depending on DJANGO_ENV, start the appropriate server
if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting in development mode with runserver..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Starting in production mode with Gunicorn..."
    exec gunicorn vocationalnyc.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
fi