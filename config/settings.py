"""Django settings for the notarial ERP."""

import os
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set.")
DEBUG = os.environ.get("DJANGO_DEBUG", "").lower() in {"1", "true", "yes"}


def _positive_setting(name, default):
    value = os.environ.get(name, str(default))
    try:
        value = int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise ImproperlyConfigured(f"{name} must be a positive integer")
    return value


_temporary_default = Path(tempfile.gettempdir()) / "notaria-expedientes"
_temporary_configured = Path(
    os.environ.get("EXPEDIENTES_TEMP_DIR", _temporary_default)
).expanduser()
if not _temporary_configured.is_absolute():
    raise ImproperlyConfigured("EXPEDIENTES_TEMP_DIR must be an absolute path")
EXPEDIENTES_TEMP_DIR = _temporary_configured.resolve()
try:
    EXPEDIENTES_TEMP_DIR.relative_to((BASE_DIR / "static").resolve())
except ValueError:
    pass
else:
    raise ImproperlyConfigured("EXPEDIENTES_TEMP_DIR cannot be served as static")
EXPEDIENTES_MAX_FILE_SIZE = _positive_setting(
    "EXPEDIENTES_MAX_FILE_SIZE", 25 * 1024 * 1024
)
EXPEDIENTES_PROCESSING_TIMEOUT = _positive_setting(
    "EXPEDIENTES_PROCESSING_TIMEOUT", 15 * 60
)
ALLOWED_HOSTS = [
    host
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host
]

INSTALLED_APPS = [
    "config.apps.ERPAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "accounts.apps.AccountsConfig",
    "core",
    "expedientes.apps.ExpedientesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.ForcePasswordChangeMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "confrontador"),
        "USER": os.environ.get("POSTGRES_USER", "confrontador"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
    }
}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.LockoutBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"
