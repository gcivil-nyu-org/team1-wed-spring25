#!/bin/bash

set -e  # Exit on first error
echo "▶ Setting up environment"

export DJANGO_SETTINGS_MODULE=vocationalnyc.settings
export PYTHONPATH=$(pwd)/VocationalNYC

cd VocationalNYC

python3.12 -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install coveralls black flake8

echo "▶ Running migrations and collecting static files"
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "▶ Running tests and linters"
python manage.py test
black --check .
flake8 .
coverage run --source=. manage.py test

echo "▶ Sending coverage to coveralls"
coveralls --verbose

echo "✅ Local CI complete"