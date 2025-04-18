"""
Django settings for vocationalnyc project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see:
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see:
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import boto3
from botocore.exceptions import ClientError

from pathlib import Path
import environ
import json


USE_TZ = True
TIME_ZONE = "America/New_York"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(DEBUG=(bool, False))
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)


def get_secret(secret_name):
    region_name = "us-east-1"

    # Create a Secrets Manager client

    session = boto3.session.Session(region_name=region_name)
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = json.loads(get_secret_value_response["SecretString"])
    return secret


DEBUG = env("DEBUG", default="False")

DJANGO_ENV = env("DJANGO_ENV", default="production")

SECRET_KEY = env("SECRET_KEY", default="insecure" if DEBUG else environ.Env.NOTSET)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=(
        [
            "127.0.0.1",
            "localhost",
            "vocationalnyc-env.eba-uurzafst.us-east-1.elasticbeanstalk.com",
            "vocationalnyc-test.us-east-1.elasticbeanstalk.com",
        ]
        if DEBUG
        else []
    ),
)

ADMINS = env.list("ADMINS", default=[("admin", "admin@example.com")] if DEBUG else [])
MANAGERS = ADMINS

EMAIL_BACKEND = (
    "django.core.mail.backends.filebased.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_FILE_PATH = BASE_DIR / "logs" / "emails"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "allauth",
    "allauth.account",
    "channels",
    "courses",
    "review",
    "message",
    "bookmarks",
    "widget_tweaks",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Authentication middleware
    "users.middleware.AdminRedirectMiddleware",
    "users.middleware.TrainingProviderMiddleware",  # Custom middleware for training provider verification
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "users.backends.TrainingProviderVerificationBackend",  # Custom backend for training provider verification
    "django.contrib.auth.backends.ModelBackend",  # Django admin login
    "allauth.account.auth_backends.AuthenticationBackend",  # allauth authentication
]

ROOT_URLCONF = "vocationalnyc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "users" / "templates" / "users",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "vocationalnyc.context_processors.intro_content",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "vocationalnyc.wsgi.application"
ASGI_APPLICATION = "vocationalnyc.asgi.application"

# Redis Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}

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
    ebdb_creds = get_secret("ebdb_creds")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default=ebdb_creds["dbname"]),
            "USER": env("POSTGRES_USER", default=ebdb_creds["username"]),
            "PASSWORD": env("POSTGRES_PASSWORD", default=ebdb_creds["password"]),
            "HOST": env("POSTGRES_HOST", default=ebdb_creds["host"]),
            "PORT": env.int("POSTGRES_PORT", default=ebdb_creds["port"]),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 30,
                "isolation_level": None,
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 9},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Security settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Django Allauth Config
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION = "none" if DEBUG else "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = False
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_ADAPTER = "users.adapters.MyAccountAdapter"

AUTH_USER_MODEL = "users.CustomUser"
ACCOUNT_FORMS = {
    "signup": "users.forms.CustomSignupForm",
}

ACCOUNT_LOGOUT_ON_GET = True

# Multi-Factor Authentication (MFA)
MFA_SUPPORTED_TYPES = ["webauthn", "totp", "recovery_codes"]
MFA_PASSKEY_LOGIN_ENABLED = True
MFA_PASSKEY_SIGNUP_ENABLED = True

# Localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"  # Ensure this starts and ends with a slash
STATICFILES_DIRS = [BASE_DIR / "static"]  # Development static files
STATIC_ROOT = BASE_DIR / "staticfiles"  # Used in production

# Serve media files in development
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Favicon Handling (Ensure favicon.ico is inside static/)
FAVICON_PATH = STATIC_URL + "favicon.ico"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"


GOOGLE_MAPS_API_KEY = env("GOOGLE_MAPS_API_KEY", default="")

# Add logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "users.views": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
