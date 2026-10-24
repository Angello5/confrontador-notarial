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
# F21: el borrador .docx se conserva como original inalterable, fuera del repo.
_originales_configured = Path(
    os.environ.get("EXPEDIENTES_ORIGINALES_DIR", Path.home() / "notaria-originales")
).expanduser()
if not _originales_configured.is_absolute():
    raise ImproperlyConfigured("EXPEDIENTES_ORIGINALES_DIR must be an absolute path")
EXPEDIENTES_ORIGINALES_DIR = _originales_configured.resolve()
if EXPEDIENTES_ORIGINALES_DIR.is_relative_to(BASE_DIR.resolve()):
    raise ImproperlyConfigured(
        "EXPEDIENTES_ORIGINALES_DIR must be outside the repository"
    )
EXPEDIENTES_MAX_FILE_SIZE = _positive_setting(
    "EXPEDIENTES_MAX_FILE_SIZE", 25 * 1024 * 1024
)
EXPEDIENTES_PROCESSING_TIMEOUT = _positive_setting(
    "EXPEDIENTES_PROCESSING_TIMEOUT", 15 * 60
)
# F61: capa de sentido. Apagada por defecto; con el interruptor apagado el ERP
# queda exactamente como antes. Los modelos se aprovisionan fuera del repositorio.
SENTIDO_ACTIVO = os.environ.get("SENTIDO_ACTIVO", "").lower() in {"1", "true", "yes"}
SENTIDO_MODELOS_DIR = (
    Path(
        os.environ.get(
            "SENTIDO_MODELOS_DIR", Path.home() / "notaria-modelos" / "sentido"
        )
    )
    .expanduser()
    .resolve()
)
SENTIDO_HILOS = _positive_setting("SENTIDO_HILOS", 3)
# Versión del ERP registrada en cada corrida; incrementar junto con
# sonar.projectVersion al publicar.
ERP_VERSION = "0.20.0"
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
# F28: nombre de la notaría en la interfaz; el real se configura en el servidor.
ERP_NOMBRE = os.environ.get("ERP_NOMBRE", "ERP Notarial")
ERP_LOGO = os.environ.get("ERP_LOGO", "").strip()
ERP_DIRECCION = os.environ.get("ERP_DIRECCION", "").strip()
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
                "core.context_processors.marca",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

_clave_db = os.environ.get("DB_PASSWORD")
if not _clave_db:
    raise ImproperlyConfigured("DB_PASSWORD must be set.")
# F63: SQL Server. Sin puerto, el driver resuelve la instancia (memoria
# compartida en local, 1433 en la red); la confianza en un certificado propio
# de la LAN se pide de forma explícita.
_confiar = os.environ.get("DB_TRUST_SERVER_CERTIFICATE", "").lower() in {
    "1",
    "true",
    "yes",
}
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.environ.get("DB_NAME", "confrontador"),
        "USER": os.environ.get("DB_USER", "confrontador"),
        "PASSWORD": _clave_db,
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", ""),
        "OPTIONS": {
            "driver": "ODBC Driver 18 for SQL Server",
            "extra_params": "Encrypt=yes;TrustServerCertificate="
            + ("yes" if _confiar else "no"),
        },
        # Distingue mayúsculas y tildes como la base de producción (research R2).
        "TEST": {"COLLATION": "Modern_Spanish_100_CS_AS"},
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
# F8: en el servidor, IIS sirve `collectstatic` desde una carpeta compartida entre versiones.
STATIC_ROOT = Path(os.environ.get("ERP_STATIC_ROOT") or BASE_DIR / "staticfiles")
# F8: archivos de estado para los avisos del Inicio del Administrador; sin ella, no hay avisos.
_estado = os.environ.get("ERP_ESTADO_DIR", "").strip()
ERP_ESTADO_DIR = Path(_estado) if _estado else None
# F8: un archivo por rol (web, worker, tarea): en Windows dos procesos no pueden
# rotar el mismo archivo. Sin carpeta, la configuración de registros de Django.
_registros = os.environ.get("ERP_REGISTROS_DIR", "").strip()
LOGGING = {"version": 1, "disable_existing_loggers": False}
if _registros:
    LOGGING |= {
        "formatters": {
            "erp": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
        },
        "handlers": {
            "archivo": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(
                    Path(_registros) / f"{os.environ.get('ERP_ROL', 'erp')}.log"
                ),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 10,
                "encoding": "utf-8",
                "formatter": "erp",
            }
        },
        "root": {"handlers": ["archivo"], "level": "INFO"},
    }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
# F62: nombres propios. Las cookies se separan por host, no por puerto: otra app
# Django en el mismo equipo borraba «sessionid» y el ERP volvía al login.
SESSION_COOKIE_NAME = "confrontador_sesion"
CSRF_COOKIE_NAME = "confrontador_csrftoken"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"
