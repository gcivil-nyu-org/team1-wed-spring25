#!/bin/sh
set -e

# Depending on DJANGO_ENV, start the appropriate server
if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting in development mode with runserver..."
    exec python manage.py runserver 0.0.0.0:5000
elif [ "$DJANGO_ENV" = "websocket_testing" ]; then
    echo "Starting in testing mode with Daphne..."
    exec daphne -b 0.0.0.0 -p 5000 vocationalnyc.asgi:application
elif [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting in production mode with Daphne..."
    exec daphne -b 0.0.0.0 -p 5000 vocationalnyc.asgi:application
else
    echo "Invalid DJANGO_ENV value. Please set to either 'development', 'testing', or 'production'."
    exit 1
fi
