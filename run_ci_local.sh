#!/bin/bash

set -e  # Exit on first error
echo "▶ Setting up environment"

export DJANGO_SETTINGS_MODULE=vocationalnyc.settings
export PYTHONPATH=$(pwd)/VocationalNYC

cd VocationalNYC

python3.12 -m venv venv
source venv/bin/activate

echo "▶ Running migrations and collecting static files"
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "▶ Running tests and linters"
python manage.py test
black --check .
flake8 . --exclude=venv
coverage run --source=. manage.py test

echo "▶ Sending coverage to coveralls"

if [[ -n "$COVERALLS_REPO_TOKEN" ]]; then
  echo "▶ Sending coverage to coveralls"
  coveralls --verbose
else
  echo "⚠️  COVERALLS_REPO_TOKEN not set; skipping coveralls upload"
fi

echo "✅ Local CI complete"