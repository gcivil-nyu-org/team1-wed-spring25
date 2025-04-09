main:[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-spring25.svg?token=dZycGtqUCL7r5eEaxTBe&branch=main)](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-spring25) [![Coverage Status][![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/team1-wed-spring25/badge.svg)](https://coveralls.io/github/gcivil-nyu-org/team1-wed-spring25)

develop:[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-spring25.svg?token=dZycGtqUCL7r5eEaxTBe&branch=develop)](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-spring25) [![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/team1-wed-spring25/badge.svg?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/team1-wed-spring25?branch=develop)

# VocationalNYC

This project is a Django-based web application configured to run using Docker. The application has been migrated from SQLite to PostgreSQL. This README outlines the steps required for local development, CI/CD testing, and production deployment—including the configuration for Docker Compose and Nginx.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
  - [Docker Compose Setup](#docker-compose-setup)
  - [Nginx Configuration](#nginx-configuration)
- [CI/CD Environment](#cicd-environment)
- [Switching Between SQLite and PostgreSQL](#switching-between-sqlite-and-postgresql)
- [Troubleshooting](#troubleshooting)
  - [Resetting the Database](#resetting-the-database)
- [Additional Notes](#additional-notes)

---

## Prerequisites

- **Docker & Docker Compose:**  
  Ensure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.
- **Python 3.12+:**  
  (For local development outside Docker, if needed.)
- **Git:**  
  To clone the repository.

---

## Environment Variables

The project uses environment variables to configure database settings, secret keys, and other configurations. Below is an example `.env` file:

```dotenv
# .env file for local development and CI/CD
DEBUG=True
DJANGO_ENV=development
SECRET_KEY=development-secret-key

# PostgreSQL settings
POSTGRES_DB=vocationalnyc_db
POSTGRES_USER=db_admin
POSTGRES_PASSWORD=secret-db-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Optionally, you can set DATABASE_URL like:
# DATABASE_URL=postgres://db_admin:secret-db-password@db:5432/vocationalnyc_db
```

For production, configure environment variables via the deployment platform (e.g., AWS Elastic Beanstalk) rather than using a `.env` file.

---

## Local Development

### Docker Compose Setup

The `docker-compose.yml` file defines the multi-container environment. An example configuration:

```yaml
# This file is used to override the docker-compose.yml file for local development and testing purposes.
services:
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: nginx
    ports:
      - "80:80"

  redis:
    image: redis:latest
    container_name: redis
    ports:
      - "6379:6379"

  app:
    build:
      context: .
      dockerfile: Dockerfile
    env_file: .env
    environment:
    #   - DJANGO_ENV=development_w/channel # Uncomment this line to test the websocket
      - DJANGO_ENV=development
    container_name: app
    depends_on:
      - redis
      - nginx
    volumes:
      - .:/vocationalnyc
    ports:
      - "5000:5000"
      
```

**Note:**  
In order to test websocket functionalities you must set `DJANGO_ENV` to `development_w/websocket`.

**Commands to Build and Run Locally:**

1. **Build the images:**

   ```bash
   docker-compose build
   ```

2. **Start the containers:**

   ```bash
   docker-compose up --build
   ```

3. **Run Migrations (if needed):**

   ```bash
   docker-compose exec app python manage.py migrate
   ```

4. **Creating a Superuser (Optional):**

   ```bash
   docker-compose exec app python manage.py createsuperuser
   ```

### Nginx Configuration

The Nginx configuration (located in the `nginx` directory) forwards requests to the Django app using Docker’s internal DNS.

**Example `nginx.conf`:**

```nginx
server {
   listen 80;
   server_name vocationalnyc-env.eba-uurzafst.us-east-1.elasticbeanstalk.com; # Replace with the domain for production or use localhost for testing
   client_max_body_size 200M;

   # Use Docker's internal DNS resolver (127.0.0.11 is fixed for Docker)
   resolver 127.0.0.11 valid=30s;

   # Standard HTTP requests
   location / {
      set $app "app:5000";
      proxy_set_header X-Url-Scheme $scheme;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header Host $http_host;
      proxy_redirect off;
      proxy_pass http://$app;
   }

   # WebSocket requests (e.g., those under /ws/)
   location /ws/ {
      set $app "app:5000";
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
      proxy_redirect off;
      proxy_pass http://$app;
   }
}
```

**Note:**  
Current configuration uses the fixed IP address of Docker's internal DNS resolver.

---

## CI/CD Environment

For the CI/CD pipeline (e.g., Travis CI):

- **Environment Variables:**  
  Configure CI/CD secrets for `SECRET_KEY`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
  
- **Build & Test Process:**  
  The CI pipeline can use Docker Compose to spin up the app and database. For example:

  ```bash
  docker-compose up --build -d
  docker-compose exec -T app python manage.py migrate
  docker-compose exec -T app python manage.py test
  ```
  
- **Important:**  
  Ensure you do not include `docker-compose.override.yml` or any development-only configurations in the CI/CD pipeline.

---

### Dockerfile

The `Dockerfile` is optimized for production and uses **Daphne** for ASGI to serve the application on port `5000`.

### Production Environment Variables

Do **not** include the `.env` file in production deployments. Instead, configure environment variables via the Elastic Beanstalk console or the CI/CD pipeline.

## Switching Between SQLite and PostgreSQL

### SQLite (for Quick Local Testing)

Modify `settings.py` to use SQLite if `DJANGO_ENV` is set as any value other than `production`.

### PostgreSQL (Default in Dockerized Configuration)

When `DJANGO_ENV` is set as `production`, use PostgreSQL. For example, in `settings.py`:

```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

# Database Configuration
if DJANGO_ENV == "travis":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "travis_ci_test",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "db",
            "PORT": 5432,
        }
    }
elif DJANGO_ENV == "production":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="db"),
            "USER": env("POSTGRES_USER", default="postgres"),
            "PASSWORD": env("POSTGRES_PASSWORD", default="postgres"),
            "HOST": env("POSTGRES_HOST", default="localhost"),
            "PORT": env.int("POSTGRES_PORT", default=5432),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

---

## Troubleshooting

### Volume Persistence

PostgreSQL data is persisted via the named volume (e.g., `postgres_data`). On Linux, this is typically stored at `/var/lib/docker/volumes/postgres_data/_data`.

### Resetting the Database

1. **Stop All Running Containers:**

   ```bash
   docker-compose down
   ```

2. **Remove All Volumes:**

   ```bash
   docker-compose down -v
   ```

3. **Remove All Containers and Images (Optional Cleanup):**

   ```bash
   docker system prune -a
   ```

4. **Delete Migration Files:**

   *(Ensure you keep `__init__.py` in each migrations folder.)*

   ```bash
   rm path/to/VocationalNYC/users/migrations/0*.py
   rm path/to/VocationalNYC/courses/migrations/0*.py
   rm path/to/VocationalNYC/review/migrations/0*.py
   rm path/to/VocationalNYC/bookmarks/migrations/0*.py
   ```

5. **Rebuild and Start Containers:**

   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   docker-compose exec app python manage.py makemigrations
   docker-compose exec app python manage.py migrate
   ```

---

## Additional Notes
  
- **Nginx and Docker DNS:**  
  The Nginx configuration uses `resolver 127.0.0.11;` to access Docker's built-in DNS for resolving container names dynamically.

- **Exposed Ports:**
  `app:5000` & `nginx:80`.

