"""Django settings for tests only."""

import os

os.environ["DJANGO_SECRET_KEY"] = "test-only-" + "not-for-deployment"
# F28: los tests prueban el nombre por defecto, nunca el del servidor.
os.environ.pop("ERP_NOMBRE", None)

from config.settings import *  # noqa: F403
