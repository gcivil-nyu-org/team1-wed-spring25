#!/bin/sh
set -e

if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting in development mode..."
    # In development, start Django's development server with hot reload enabled
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Starting in production mode..."
    exec gunicorn vocationalnyc.wsgi:application --bind 0.0.0.0:5000
fi
