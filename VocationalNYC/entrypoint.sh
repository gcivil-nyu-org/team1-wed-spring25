#!/bin/sh
set -e

# Depending on DJANGO_ENV, start the appropriate server
if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting in development mode with runserver..."
    exec python manage.py runserver 0.0.0.0:5000
else
    echo "Starting in production mode with Daphne..."
    exec daphne -b 0.0.0.0 -p 5000 vocationalnyc.asgi:application
fi
