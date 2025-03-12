#!/bin/sh
set -e

if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting in development mode with Runserver..."
    exec python manage.py runserver 0.0.0.0:8000
elif [ "$DJANGO_ENV" = "wobsocket_testing" ]; then
    echo "Starting in development mode with Daphne..."
    exec daphne -b 0.0.0.0 -p 8000 vocationalnyc.asgi:application
else
    echo "Starting in production mode with Daphne..."
    exec daphne -b 0.0.0.0 -p 5000 vocationalnyc.asgi:application
fi
