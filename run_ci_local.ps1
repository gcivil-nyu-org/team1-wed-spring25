$ErrorActionPreference = "Stop"  # Similar to set -e
Write-Host "Setting up environment"

$env:DJANGO_SETTINGS_MODULE = "vocationalnyc.settings"
$env:PYTHONPATH = "$(Get-Location)\VocationalNYC"

Set-Location -Path ".\VocationalNYC"

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "▶ Running migrations and collecting static files"
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

Write-Host "▶ Running tests and linters"
python -m black .
python -m flake8 . --exclude=venv
python -m coverage run --source=. manage.py test

if ($env:COVERALLS_REPO_TOKEN) {
    Write-Host "▶ Sending coverage to coveralls"
    python -m coveralls --verbose
} else {
    Write-Host "⚠️  COVERALLS_REPO_TOKEN not set; skipping coveralls upload"
}

Write-Host "✅ Local CI complete"
